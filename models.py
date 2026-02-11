from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Todo(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True,index=True)
    title=Column(String)
    description=Column(String)
    priority=Column(Integer)
    complete=Column(Boolean, default=False)
    owner_id=Column(Integer,ForeignKey("Users.id"))

class User(Base):
    __tablename__="Users"
    id=Column(Integer,primary_key=True,index=True)
    email=Column(String,unique=True)
    username=Column(String,unique=True)
    first_name=Column(String)
    last_name=Column(String)
    hashed_password=Column(String)
    is_active=Column(Boolean, default=True)
    role=Column(String)
    phone_number=Column(String)

