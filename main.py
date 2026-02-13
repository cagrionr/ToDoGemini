from fastapi import FastAPI,Request, Depends, Path, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from starlette.responses import RedirectResponse

from .models import Base, Todo
from .database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from .Routers.auth import router as auth_router
from .Routers.todo import router as todo_router
from fastapi.staticfiles import StaticFiles
import os



app=FastAPI()
script_directory=os.path.dirname(__file__)
st_abs_file_path=os.path.join(script_directory,"static/")



app.mount("/static",StaticFiles(directory=st_abs_file_path),name="static")

@app.get("/")
def read_root(request:Request,status_code=status.HTTP_302_FOUND):
    return RedirectResponse(url="/todo/todo_page")


app.include_router(auth_router)
app.include_router(todo_router)

Base.metadata.create_all(engine)
