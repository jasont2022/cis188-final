from fastapi import FastAPI, Body, HTTPException, Form, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio

app = FastAPI()
# templates = Jinja2Templates(directory="/templates")
client =  motor.motor_asyncio.AsyncIOMotorClient(
    "mongodb+srv://jastran:imbooster456@cluster0.ceer1.mongodb.net/blog?retryWrites=true&w=majority"
)
db = client.blog

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Post(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    author: str = Field(...)
    title: str = Field(...)
    text: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "author": "jason",
                "title": "CIS 188",
                "text": "the coolest class",
            }
        }


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user: str = Field(...)
    posts: Optional[List[Post]] = []

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {"example": {"user": "jason", "posts": []}}

class UpdatePost(BaseModel):
    author: Optional[str]
    title: Optional[str]
    text: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "author": "jason",
                "title": "CIS 188",
                "text": "the coolest class",
            }
        }

class UpdateUser(BaseModel):
    user: Optional[str]
    posts: Optional[List[Post]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {"example": {"user": "jason", "posts": []}}


@app.get("/hello")
def hello_view(name: str = "Jason"):
    return {"message": f"Hello there, {name}!"}


# home page (display all posts)
@app.get("/")
async def fetch_posts(request: Request):
    posts = await db["posts"].find().to_list(1000)
    print(posts)
    # return {
    #     "message": "successfully retrieve posts",
    #     "request": request,
    #     "posts": posts,
    # }
    return posts


# create a user
@app.post("/signup")
async def create_user(request: Request, user: User = Body(...)):
    user = jsonable_encoder(user)
    new_user = await db["user"].insert_one(user)
    created_user = await db["user"].find_one({"_id": new_user.inserted_id})
    print(created_user)
    # return {
    #     "message": "successfully created a new user",
    #     "request": request,
    #     "new_user": created_user,
    # }
    return created_user


# get a user (show user's posts)
@app.get("/user/{name}")
async def get_user(request: Request, name: str):
    if (user := await db["user"].find_one({"user": name})) is not None:
        user_posts = user['posts']
        return user_posts
    raise HTTPException(status_code=404, detail=f"User with {name} not found")

# read a post (show a single post)
@app.get("/post/{id}", response_model=Post)
async def get_post(request: Request, id: str):
    if (post := await db["post"].find_one({"_id": id})) is not None:
        return post
    raise HTTPException(status_code=404, detail=f"Post with {id} not found")


# create a post
@app.post("/user/{name}/post/create", response_model=Post)
async def create_post(request: Request, name: str, post: Post = Body(...)):
    post = jsonable_encoder(post)
    new_post = await db["post"].insert_one(post)
    created_post = await db["post"].find_one({"_id": new_post.inserted_id})

    # update user post array
    user =  await db["user"].find_one({"user": name})
    new_posts = user['posts'].append(post)
    print(created_post)
    # return {
    #     "message": "successfully created a new user",
    #     "request": request,
    #     "new_user": created_user,
    # }
    # return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)
    return created_post


# edit a post
@app.put("/user/{name}/post/{id}/edit")
def edit_post(request: Request):
    return {}


# delete a post
@app.delete("user/{name}/post/{id}/delete")
async def delete_post(request: Request, name: str, id: str):
    delete_result = await db["post"].delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return {
            "message": "successfully deleted the post"
        }
    raise HTTPException(status_code=404, detail=f"Post with {id} not found")
