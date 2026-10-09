from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    supabase_url:str
    supabase_anon_key:str
    supabase_service_role_key:str
    database_url:str
    cors_origins:str='http://localhost:5173'
    mov_bucket:str='project-mov'
    max_mov_mb:int=10
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
settings=Settings()
