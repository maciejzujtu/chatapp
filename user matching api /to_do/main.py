from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
import models
from db import engine, SessionLocal
from pydantic import BaseModel, Field

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
@app.get("/")
async def read_all(db: db_dependency  ):
    return db.query(models.Task).all()

class ToDoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str
    done: bool

@app.post("/users/")
async def create_user(db: db_dependency,todo_request: ToDoRequest):
    model = models.Task(**todo_request.model_dump())
    db.add(model)
    db.commit()


