from psycopg.rows import dict_row
from ..database import pool

def project_select(where='true',params=()):
    with pool.connection() as c:
        return c.execute(f'''select id,project_code,project_name,description,project_type,sector,status,completion_percentage,budget,contract_amount,funding_source,contractor,contract_reference,implementing_agency,location_name,barangay,city,province,start_date,target_end_date,actual_completion_date,created_at,updated_at,ST_AsGeoJSON(geometry)::json as geometry from public.projects where {where} order by updated_at desc''',params).fetchall()
def get_project(pid):
    with pool.connection() as c:
        return c.execute('''select id,project_code,project_name,description,project_type,sector,status,completion_percentage,budget,contract_amount,funding_source,contractor,contract_reference,implementing_agency,location_name,barangay,city,province,start_date,target_end_date,actual_completion_date,created_at,updated_at,ST_AsGeoJSON(geometry)::json as geometry from public.projects where id=%s''',(pid,)).fetchone()
def rowdict(row):
    if not row:return None
    d=dict(row) if isinstance(row,dict) else None
    if d is not None:return d
    cols=['id','project_code','project_name','description','project_type','sector','status','completion_percentage','budget','contract_amount','funding_source','contractor','contract_reference','implementing_agency','location_name','barangay','city','province','start_date','target_end_date','actual_completion_date','created_at','updated_at','geometry']
    return dict(zip(cols,row))
