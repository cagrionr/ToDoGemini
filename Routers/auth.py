from fastapi import APIRouter,Request,Depends, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from starlette import status

from ..database import SessionLocal
from ..models import User
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import timedelta,datetime,timezone


router=APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

templates=Jinja2Templates(directory="app/templates")

SECRET_KEY="hfn60ajwxnrxukc163csg8wciai0rngh9tmfblgr91x7gab7c1h20thb0lunras8"
ALGORITHM="HS256"


bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency=Annotated[Session, Depends(get_db)]
oauth2_bearer=OAuth2PasswordBearer(tokenUrl="/auth/token")


class CreateUserRequest(BaseModel):
    username:str
    email:str
    first_name:str
    last_name:str
    password:str
    role:str
    phone_number:str

class Token(BaseModel):
    access_token:str
    token_type:str



def create_access_token(username:str, user_id:int, role:str, expires_delta:timedelta):
    payload={"sub":username, "id": user_id, "role":role}
    expires=datetime.now(timezone.utc)+expires_delta
    payload.update({"exp":expires})
    return jwt.encode(payload,SECRET_KEY, algorithm=ALGORITHM)



def authenticate_user(db:db_dependency,username:str, password:str):
    user=db.query(User).filter(User.username==username).first()
    if not user :
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

async def get_current_user(token:Annotated[str,Depends(oauth2_bearer)]):
    try:
        payload= jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username=payload.get("sub")
        user_id=payload.get("id")
        user_role=payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Böyle bir kullanıcı bulunamadı.")
        return {"username":username,"user_id":user_id,"user_role":user_role}
    except JWTError:
        raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Bu token geçersizdir.")


@router.post("/token",response_model=Token)
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm, Depends()],db:db_dependency):
    user=authenticate_user(db=db,username=form_data.username,password=form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="incorret username or password")
    token=create_access_token(user.username,user.id,user.role,timedelta(minutes=60))
    return {"access_token":token,"token_type":"bearer"}


@router.get("/login_page")
def render_login_page(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})


@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency,create_user_request:CreateUserRequest):
    user=User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        phone_number=create_user_request.phone_number
    )

    db.add(user)
    db.commit()

