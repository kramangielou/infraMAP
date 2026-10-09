from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Form
from datetime import date
from pathlib import PurePosixPath
from uuid import UUID,uuid4
import json
from ..database import pool
from ..auth import current_user,admin_required
from ..schemas.common import ProjectCreate,ProjectUpdate
from ..services.geo import validate_geometry
from ..services.storage import upload,signed_url,remove
from ..config import settings
router=APIRouter(tags=['projects'])

def filters(year=None,status=None,project_type=None,location=None,agency=None,search=None):
    w=['p.archived_at is null']; params=[]
    if year: w.append('extract(year from p.start_date)=%s');params.append(int(year))
    if status: w.append('p.status=%s');params.append(status)
    if project_type: w.append('p.project_type ilike %s');params.append(f'%{project_type}%')
    if location: w.append("concat_ws(' ',p.location_name,p.barangay,p.city,p.province) ilike %s");params.append(f'%{location}%')
    if agency: w.append('p.implementing_agency ilike %s');params.append(f'%{agency}%')
    if search: w.append("concat_ws(' ',p.project_code,p.project_name,p.contractor,p.location_name,p.implementing_agency) ilike %s");params.append(f'%{search}%')
    return ' and '.join(w),params

def serialize(row):
    d=dict(row);return d
@router.get('/projects')
def list_projects(year:str|None=None,status:str|None=None,project_type:str|None=None,location:str|None=None,agency:str|None=None,search:str|None=None,page:int=1,page_size:int=20,sort_by:str='updated_at',sort_dir:str='desc',user=Depends(current_user)):
    w,params=filters(year,status,project_type,location,agency,search)
    allowed_sort={'updated_at','project_name','project_code','status','budget','completion_percentage','start_date','target_end_date'}
    if sort_by not in allowed_sort: sort_by='updated_at'
    sort_dir='asc' if sort_dir.lower()=='asc' else 'desc'
    page=max(1,page);page_size=min(100,max(1,page_size));offset=(page-1)*page_size
    with pool.connection() as c:
        total=c.execute(f'''select count(*) as count from public.projects p where {w}''',params).fetchone()['count']
        rows=c.execute(f'''select p.id,p.project_code,p.project_name,p.description,p.project_type,p.sector,p.status,p.completion_percentage,p.budget,p.contract_amount,p.funding_source,p.contractor,p.contract_reference,p.implementing_agency,p.location_name,p.barangay,p.city,p.province,p.start_date,p.target_end_date,p.actual_completion_date,p.created_at,p.updated_at,ST_AsGeoJSON(p.geometry)::json as geometry from public.projects p where {w} order by p.{sort_by} {sort_dir} limit %s offset %s''',params+[page_size,offset]).fetchall()
        return {'items':[serialize(r) for r in rows],'total':total,'page':page,'page_size':page_size}
@router.get('/projects/{project_id}')
def get_project(project_id:UUID,user=Depends(current_user)):
    with pool.connection() as c:
        r=c.execute('''select p.id,p.project_code,p.project_name,p.description,p.project_type,p.sector,p.status,p.completion_percentage,p.budget,p.contract_amount,p.funding_source,p.contractor,p.contract_reference,p.implementing_agency,p.location_name,p.barangay,p.city,p.province,p.start_date,p.target_end_date,p.actual_completion_date,p.created_at,p.updated_at,ST_AsGeoJSON(p.geometry)::json as geometry from public.projects p where p.id=%s and p.archived_at is null''',(project_id,)).fetchone()
    if not r:raise HTTPException(404,'Project not found')
    return serialize(r)

def write_project(data,project_id=None,user_id=None):
    try:validate_geometry(data.get('geometry'))
    except ValueError as e:raise HTTPException(422,str(e))
    vals=data.copy();g=vals.pop('geometry',None)
    if project_id:
        sets=[];params=[]
        for k,v in vals.items():sets.append(f'{k}=%s');params.append(v)
        sets += ['geometry=case when %s::text is null then null else ST_SetSRID(ST_GeomFromGeoJSON(%s::text),4326) end','updated_by=%s','updated_at=now()'];params += [json.dumps(g) if g is not None else None,json.dumps(g) if g is not None else None,user_id,project_id]
        with pool.connection() as c:c.execute(f'update public.projects set {", ".join(sets)} where id=%s',params);c.commit()
        return get_project(project_id,user=None)
    cols=list(vals.keys())+['geometry','created_by','updated_by'];place=['%s']*len(vals)+['case when %s::text is null then null else ST_SetSRID(ST_GeomFromGeoJSON(%s::text),4326) end','%s','%s'];params=list(vals.values())+[json.dumps(g) if g is not None else None,json.dumps(g) if g is not None else None,user_id,user_id]
    with pool.connection() as c:
        r=c.execute(f'insert into public.projects ({", ".join(cols)}) values ({", ".join(place)}) returning id',params).fetchone();c.commit();pid=r['id']
    return get_project(pid,user=None)
@router.post('/projects')
def create_project(data:ProjectCreate,user=Depends(admin_required)):
    return write_project(data.model_dump(mode='json'),user_id=user['id'])
@router.put('/projects/{project_id}')
def update_project(project_id:UUID,data:ProjectUpdate,user=Depends(admin_required)):
    with pool.connection() as c:
        if not c.execute('select 1 from public.projects where id=%s and archived_at is null',(project_id,)).fetchone():raise HTTPException(404,'Project not found')
    return write_project(data.model_dump(mode='json'),project_id,user['id'])
@router.delete('/projects/{project_id}')
def delete_project(project_id:UUID,user=Depends(admin_required)):
    with pool.connection() as c:c.execute('update public.projects set archived_at=now(),updated_by=%s,updated_at=now() where id=%s',(user['id'],project_id));c.commit()
    return {'ok':True}

@router.get('/projects/{project_id}/progress')
def progress(project_id:UUID,user=Depends(current_user)):
    with pool.connection() as c:
        rows=c.execute('''select pp.id,pp.project_id,pp.progress_percentage,pp.progress_date,pp.remarks,pp.recorded_by,pp.created_at from public.project_progress pp where pp.project_id=%s order by pp.progress_date desc,pp.created_at desc''',(project_id,)).fetchall()
        out=[]
        for r in rows:
            d=dict(r); ms=c.execute('''select id,project_id,progress_id,file_name,file_path,file_type,file_size,caption,taken_at,uploaded_by,created_at from public.project_progress_media where progress_id=%s order by created_at''',(r['id'],)).fetchall()
            d['media']=[]
            for m in ms:
                md=dict(m);md['public_url']=signed_url(md['file_path']);d['media'].append(md)
            out.append(d)
    return out

ALLOWED_TYPES={'image/jpeg','image/png','image/webp'};ALLOWED_EXT={'.jpg','.jpeg','.png','.webp'}
@router.post('/projects/{project_id}/progress')
async def add_progress(project_id:UUID,progress_percentage:float=Form(...),progress_date:date=Form(...),remarks:str|None=Form(None),captions:str|None=Form(None),taken_dates:str|None=Form(None),files:list[UploadFile]=File(default=[]),user=Depends(admin_required)):
    if not 0<=progress_percentage<=100:raise HTTPException(422,'Progress must be between 0 and 100')
    with pool.connection() as c:
        if not c.execute('select 1 from public.projects where id=%s and archived_at is null',(project_id,)).fetchone():raise HTTPException(404,'Project not found')
        r=c.execute('''insert into public.project_progress(project_id,progress_percentage,progress_date,remarks,recorded_by) values(%s,%s,%s,%s,%s) returning id''',(project_id,progress_percentage,progress_date,remarks,user['id'])).fetchone();progress_id=r['id']
        c.execute('update public.projects set completion_percentage=%s,updated_by=%s,updated_at=now() where id=%s',(progress_percentage,user['id'],project_id));c.commit()
    warnings=[];media=[]
    try: caption_list=json.loads(captions) if captions else []
    except Exception: caption_list=[]
    try: taken_list=json.loads(taken_dates) if taken_dates else []
    except Exception: taken_list=[]
    for idx,f in enumerate(files):
        ext=PurePosixPath(f.filename or '').suffix.lower()
        data=await f.read()
        if f.content_type not in ALLOWED_TYPES or ext not in ALLOWED_EXT:warnings.append(f'{f.filename}: unsupported image type');continue
        if len(data)>settings.max_mov_mb*1024*1024:warnings.append(f'{f.filename}: exceeds {settings.max_mov_mb} MB');continue
        path=f'{project_id}/{progress_id}/{uuid4()}{ext}'
        try:
            upload(path,data,f.content_type)
            with pool.connection() as c:
                m=c.execute('''insert into public.project_progress_media(project_id,progress_id,file_name,file_path,file_type,file_size,caption,taken_at,uploaded_by) values(%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id,project_id,progress_id,file_name,file_path,file_type,file_size,caption,taken_at,uploaded_by,created_at''',(project_id,progress_id,f.filename,path,f.content_type,len(data),caption_list[idx] if idx<len(caption_list) else None,taken_list[idx] if idx<len(taken_list) and taken_list[idx] else None,user['id'])).fetchone();c.commit()
            md=dict(m);md['public_url']=signed_url(path);media.append(md)
        except Exception as e:warnings.append(f'{f.filename}: upload failed')
    if files and not media and warnings:
        warnings.append('Progress was saved, but no MOV files were uploaded.')
    return {'id':str(progress_id),'project_id':str(project_id),'progress_percentage':progress_percentage,'progress_date':progress_date,'remarks':remarks,'recorded_by':user['id'],'media':media,'warnings':warnings}
@router.delete('/progress-media/{media_id}')
def delete_media(media_id:UUID,user=Depends(admin_required)):
    with pool.connection() as c:
        r=c.execute('select file_path from public.project_progress_media where id=%s',(media_id,)).fetchone()
        if not r:raise HTTPException(404,'Media not found')
        c.execute('delete from public.project_progress_media where id=%s',(media_id,));c.commit()
    try:remove(r['file_path'])
    except Exception:pass
    return {'ok':True}