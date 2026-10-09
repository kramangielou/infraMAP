from supabase import create_client
from ..config import settings
client=create_client(settings.supabase_url,settings.supabase_service_role_key)
def upload(path:str,data:bytes,content_type:str):
    return client.storage.from_(settings.mov_bucket).upload(path,data,{'content-type':content_type,'upsert':False})
def signed_url(path:str,seconds=3600):
    return client.storage.from_(settings.mov_bucket).create_signed_url(path,seconds)['signedURL']
def remove(path:str):
    client.storage.from_(settings.mov_bucket).remove([path])
