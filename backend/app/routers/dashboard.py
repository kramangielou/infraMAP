from fastapi import APIRouter,Depends
from ..auth import current_user
from ..database import pool
from .projects import filters
router=APIRouter(prefix='/dashboard',tags=['dashboard'])
def run_filter(year,status,project_type,location,agency,search):return filters(year,status,project_type,location,agency,search)
@router.get('/summary')
def summary(year:str|None=None,status:str|None=None,project_type:str|None=None,location:str|None=None,agency:str|None=None,search:str|None=None,user=Depends(current_user)):
    w,p=run_filter(year,status,project_type,location,agency,search)
    with pool.connection() as c:
        r=c.execute(f'''select count(*) total_projects,count(*) filter(where status='COMPLETED') completed_projects,count(*) filter(where status='ONGOING') ongoing_projects,count(*) filter(where status='PENDING') pending_projects,count(*) filter(where status='DELAYED') delayed_projects,count(*) filter(where status='SUSPENDED') suspended_projects,coalesce(sum(budget),0) total_budget,coalesce(avg(completion_percentage),0) average_completion,count(*) filter(where target_end_date between current_date and current_date+interval '30 days' and completion_percentage<100) projects_due_soon,count(*) filter(where target_end_date<current_date and completion_percentage<100) projects_overdue from public.projects p where {w}''',p).fetchone();d=dict(r);d['completion_rate']=round((d['completed_projects']/d['total_projects']*100) if d['total_projects'] else 0,2);return d
@router.get('/projects-by-year')
def by_year(year:str|None=None,status:str|None=None,project_type:str|None=None,location:str|None=None,agency:str|None=None,search:str|None=None,user=Depends(current_user)):
    w,p=run_filter(year,status,project_type,location,agency,search)
    with pool.connection() as c:return [dict(r) for r in c.execute(f'''select extract(year from start_date)::int as year,count(*) total_projects,count(*) filter(where status='COMPLETED') completed_projects from public.projects p where {w} group by 1 order by 1''',p).fetchall()]
@router.get('/projects-by-status')
def by_status(year:str|None=None,status:str|None=None,project_type:str|None=None,location:str|None=None,agency:str|None=None,search:str|None=None,user=Depends(current_user)):
    w,p=run_filter(year,status,project_type,location,agency,search)
    with pool.connection() as c:return [dict(r) for r in c.execute(f'''select status,count(*) from public.projects p where {w} group by status order by status''',p).fetchall()]
@router.get('/projects-by-sector')
def by_sector(year:str|None=None,status:str|None=None,project_type:str|None=None,location:str|None=None,agency:str|None=None,search:str|None=None,user=Depends(current_user)):
    w,p=run_filter(year,status,project_type,location,agency,search)
    with pool.connection() as c:return [dict(r) for r in c.execute(f'''select sector,count(*) from public.projects p where {w} group by sector order by count(*) desc''',p).fetchall()]
@router.get('/recent-updates')
def recent(year:str|None=None,status:str|None=None,project_type:str|None=None,location:str|None=None,agency:str|None=None,search:str|None=None,user=Depends(current_user)):
    w,p=run_filter(year,status,project_type,location,agency,search)
    with pool.connection() as c:return [dict(r) for r in c.execute(f'''select pp.id,pp.project_id,p.project_name,pp.progress_percentage,pp.progress_date,pp.remarks,(select count(*) from public.project_progress_media m where m.progress_id=pp.id)::int media_count from public.project_progress pp join public.projects p on p.id=pp.project_id where {w.replace('p.','p.')} order by pp.progress_date desc,pp.created_at desc limit 8''',p).fetchall()]