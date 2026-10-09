import httpx
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from .config import settings
from .database import pool
bearer=HTTPBearer(auto_error=False)
async def current_user(creds:HTTPAuthorizationCredentials|None=Depends(bearer)):
    if not creds: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Authentication required')
    try:
        async with httpx.AsyncClient() as client:
            r=await client.get(f'{settings.supabase_url}/auth/v1/user',headers={'apikey':settings.supabase_anon_key,'Authorization':f'Bearer {creds.credentials}'},timeout=8)
    except Exception: raise HTTPException(status_code=401,detail='Unable to validate session')
    if r.status_code!=200: raise HTTPException(status_code=401,detail='Invalid or expired session')
    user=r.json()
    with pool.connection() as c:
        row=c.execute('select id,full_name,role from public.profiles where id=%s',(user['id'],)).fetchone()
    if not row: raise HTTPException(status_code=403,detail='Profile is not configured')
    return {'id':str(row['id']),'full_name':row['full_name'],'role':row['role']}
def admin_required(user=Depends(current_user)):
    if user['role']!='ADMIN': raise HTTPException(status_code=403,detail='Admin permission required')
    return user
