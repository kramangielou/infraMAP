from fastapi import APIRouter,Depends
from ..auth import current_user
router=APIRouter(tags=['auth'])
@router.get('/me')
def me(user=Depends(current_user)):return user
