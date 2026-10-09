from pydantic import BaseModel,Field,field_validator
from datetime import date
from typing import Any
STATUSES={'PENDING','ONGOING','COMPLETED','DELAYED','SUSPENDED'}
class ProjectBase(BaseModel):
    project_code:str=Field(min_length=1,max_length=80); project_name:str=Field(min_length=1,max_length=255); description:str|None=None
    project_type:str=Field(min_length=1,max_length=100); sector:str=Field(min_length=1,max_length=100); status:str='PENDING'
    completion_percentage:float=Field(ge=0,le=100); budget:float=Field(ge=0); contract_amount:float|None=Field(default=None,ge=0)
    funding_source:str|None=None; contractor:str|None=None; contract_reference:str|None=None; implementing_agency:str|None=None
    location_name:str|None=None; barangay:str|None=None; city:str|None=None; province:str|None=None
    start_date:date|None=None; target_end_date:date|None=None; actual_completion_date:date|None=None; geometry:dict[str,Any]|None=None
    @field_validator('status')
    @classmethod
    def status_ok(cls,v):
        if v not in STATUSES: raise ValueError('Invalid project status')
        return v
    @field_validator('actual_completion_date')
    @classmethod
    def actual_not_before_start(cls,v,info):
        st=info.data.get('start_date')
        if v and st and v<st: raise ValueError('actual_completion_date must be on/after start_date')
        return v
    @field_validator('target_end_date')
    @classmethod
    def target_after_start(cls,v,info):
        st=info.data.get('start_date')
        if v and st and v<st: raise ValueError('target_end_date must be on/after start_date')
        return v
class ProjectUpdate(ProjectBase): pass
class ProjectCreate(ProjectBase): pass
class GeometryIn(BaseModel): type:str;coordinates:Any
class ProgressIn(BaseModel):
    progress_percentage:float=Field(ge=0,le=100); progress_date:date; remarks:str|None=None
class ProfileOut(BaseModel): id:str;full_name:str|None;role:str
