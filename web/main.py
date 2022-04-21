from typing import List, Optional

import motor.motor_asyncio
from bson import ObjectId
from fastapi import Body, FastAPI, Form, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI()
# templates = Jinja2Templates(directory="/templates")
client = motor.motor_asyncio.AsyncIOMotorClient(
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


@app.get("/hello")
def hello_view(name: str = "Jason"):
    return {"message": f"Hello there, {name}!"}


# home page (display all posts)
@app.get("/")
async def fetch_posts(request: Request):
    posts = await db["post"].find().to_list(1000)
    return {
        "message": "successfully retrieve posts",
        "posts": posts,
    }


# create a user
@app.post("/signup")
async def create_user(request: Request, user: User = Body(...)):
    user = jsonable_encoder(user)
    new_user = await db["user"].insert_one(user)
    created_user = await db["user"].find_one({"_id": new_user.inserted_id})
    return {
        "message": "successfully created a new user",
        "new_user": created_user,
    }


# get a user (show user's posts)
@app.get("/user/{name}")
async def get_user(request: Request, name: str):
    if (user := await db["user"].find_one({"user": name})) is not None:
        user_posts = user["posts"]
        return {
            "message": f"successfully retrevied {name}'s posts",
            "user_posts": user_posts,
        }
    raise HTTPException(status_code=404, detail=f"User with {name} not found")


# read a post (show a single post)
@app.get("/post/{id}")
async def get_post(request: Request, id: str):
    if (post := await db["post"].find_one({"_id": id})) is not None:
        return {
            "message": f"successfully retrevied post {id}",
            "post": post,
        }
    raise HTTPException(status_code=404, detail=f"Post with {id} not found")


# create a post
@app.post("/user/{name}/post")
async def create_post(request: Request, name: str, post: Post = Body(...)):
    if (user := await db["user"].find_one({"user": name})) is not None:
        # insert the post document to the collection
        post = jsonable_encoder(post)
        new_post = await db["post"].insert_one(post)
        created_post = await db["post"].find_one({"_id": new_post.inserted_id})

        # update user posts array
        post_list = list(user["posts"])
        post_list.append(created_post)
        await db["user"].update_one({"user": name}, {"$set": {"posts": post_list}})

        return {
            "message": "successfully created a new post",
            "new_post": created_post,
        }
    raise HTTPException(status_code=404, detail=f"User with {name} not found")


# edit a post
@app.put("/user/{name}/post/{id}")
async def edit_post(request: Request, name: str, id: str, post: UpdatePost = Body(...)):
    if (user := await db["user"].find_one({"user": name})) is not None:
        if (old_post := await db["post"].find_one({"_id": id})) is not None:
            post = {k: v for k, v in post.dict().items() if v is not None}

            # edit the post itself
            await db["post"].update_one({"_id": id}, {"$set": post})
            modified_post = await db["post"].find_one({"_id": id})

            # update user posts array
            user = await db["user"].find_one({"user": name})
            post_list = list(user["posts"])
            post_list.remove(old_post)
            post_list.append(modified_post)
            await db["user"].update_one({"user": name}, {"$set": {"posts": post_list}})

            return {
                "message": f"successfully modfided the post {id}",
                "modified_post": modified_post,
            }
        else:
            raise HTTPException(status_code=404, detail=f"Post with {id} not found")
    raise HTTPException(status_code=404, detail=f"User with {name} not found")


# delete a post
@app.delete("/user/{name}/post/{id}")
async def delete_post(request: Request, name: str, id: str):
    if (user := await db["user"].find_one({"user": name})) is not None:
        if (old_post := await db["post"].find_one({"_id": id})) is not None:

            # delete a post
            await db["post"].delete_one({"_id": id})

            # update user posts array
            user = await db["user"].find_one({"user": name})
            post_list = list(user["posts"])
            post_list.remove(old_post)
            await db["user"].update_one({"user": name}, {"$set": {"posts": post_list}})

            return {"message": f"successfully deleted the post {id}"}
        else:
            raise HTTPException(status_code=404, detail=f"Post with {id} not found")
    raise HTTPException(status_code=404, detail=f"User with {name} not found")
