from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from db import  Base

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    info = Column(String)

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    done = Column(Boolean, default=False)