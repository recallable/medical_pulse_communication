from fastapi import APIRouter

user_router = APIRouter(prefix='/user')


@user_router.post('/login')
def login():
    return {'message': 'login'}
