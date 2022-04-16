# import motor.motor_asyncio
from fastapi import FastAPI, Body, HTTPException, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List
from pymongo import MongoClient

app = FastAPI()
# templates = Jinja2Templates(directory="/templates")
client = MongoClient(
    "mongodb+srv://jastran:imbooster456@cluster0.ceer1.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
)
print(client)
db = client.blog
print(db)

# create classes using BaseModel
class Post(BaseModel):
    author: str = Field(...)
    title: str = Field(...)
    text: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "author": "jason",
                "title": "CIS 188",
                "text": "the coolest class",
            }
        }


class User(BaseModel):
    user: str = Field(...)
    posts: Optional[List[Post]] = []

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {"example": {"user": "jason", "posts": []}}


@app.get("/hello")
def hello_view(name: str = "Jason"):
    return {"message": f"Hello there, {name}!"}


# home page (display all posts)
@app.get("/", response_model=Post)
def fetch_posts(request: Request):
    posts = db["posts"].find()
    return {
        "message": "successfully retrieve posts",
        "request": request,
        "posts": posts,
    }


# create a user
@app.post("/signup", response_model=User)
def create_user(request: Request, user: User):
    user = jsonable_encoder(user)
    new_user = db["user"].insert_one(user)
    created_user = db["user"].find_one({"_id": new_user.inserted_id})
    return {
        "message": "successfully created a new user",
        "request": request,
        "new_user": created_user,
    }


# get a user (show user's posts)
@app.get("/")
def get_user(request: Request):
    return {}


# create a post
@app.post("/")
def create_post(request: Request):
    return {}


# edit a post
@app.put("/")
def edit_post(request: Request):
    return {}


# read a post (show a single post)
@app.get("/")
def get_post(request: Request):
    return {}


# delete a post
@app.delete("/")
def delete_post(request: Request):
    return {}
