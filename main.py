from fastapi import FastAPI, Depends, Path, HTTPException
from pydantic import BaseModel, Field
from starlette import status
from models import Base, Todo
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from Routers.auth import router as auth_router
from Routers.todo import router as todo_router

app=FastAPI()
app.include_router(auth_router)
app.include_router(todo_router)

Base.metadata.create_all(engine)
