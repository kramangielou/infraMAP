from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_pool,close_pool
from .routers import projects,dashboard,users
app=FastAPI(title='infraMAP API',version='0.1.0',description='Infrastructure project monitoring API')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(',') if x.strip()],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
@app.on_event('startup')
def startup():init_pool()
@app.on_event('shutdown')
def shutdown():close_pool()
@app.get('/health')
def health():return {'status':'ok'}
app.include_router(users.router);app.include_router(projects.router);app.include_router(dashboard.router)
