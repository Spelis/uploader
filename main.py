import os
from datetime import datetime, timezone
from typing import Annotated, Any
from dotenv import load_dotenv
from fastapi import Depends, Response
from fastapi import FastAPI as FA
from fastapi import HTTPException, Security, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose.exceptions import JWTError
from jose.jwt import decode, encode
from pydantic import BaseModel
from sqlmodel import select
import random
from PIL import Image
import base64

from db import File, SessionDep, User, UserCredentials, get_files_by_user

security = HTTPBearer()

CredentialsDependency = Annotated[HTTPAuthorizationCredentials, Depends(security)]

jwt_secret = "secret"  # Load this from env or some shit


def generate_jwt_token(user: User) -> str:
    payload = {
        "sub": user.username,
        "iat": datetime.now(timezone.utc).timestamp(),
    }
    return encode(payload, jwt_secret, algorithm="HS256")


async def get_user_session(db: SessionDep, credentials: CredentialsDependency) -> User:
    token = credentials.credentials
    try:
        payload = decode(token, jwt_secret, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_name = payload["sub"]
    user = (await db.exec(select(User).where(User.username == user_name))).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

def get_filepath(id:int,name:str):
    os.makedirs(f"files/{id}/", exist_ok=True)
    return f"files/{id}/{name}"

def get_existing_filepath(id:int,name:str):
    os.makedirs(f"files/{id}/", exist_ok=True) # avoid errors
    return f"files/{id}/{name}"


UserDependency = Annotated[User, Depends(get_user_session)]


app = FA()


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.post("/me")  # requires auth
async def user_info(user: UserDependency):
    #return user
    filesobj = {}
    files_iter:list[File] = await get_files_by_user(user.id)
    for i in files_iter:
        filesobj[i.filename] = {
            "id": i.id,
            "created_at": datetime.fromtimestamp(i.uploaded_at,timezone.utc).strftime(r"%a %b %d %Y %I:%M:%S %p")
        }
    return {"passwd": user.password, "username": user.username, "ID": user.id, "files": filesobj, "help":[
        "POST /login",
        "POST /register",
        "POST /me",
        "POST /up/{fmt}/{name}",
        "POST /del/{name}",
        "GET  /files/{id}/{file}"
    ]}


@app.post("/login")
async def signin(credentials: UserCredentials, session: SessionDep):
    # PK is id, but we have username
    user = (
        await session.exec(select(User).where(User.username == credentials.username))
    ).first()
    if user is None:
        return {"error": "Invalid credentials"}
    if user.password != credentials.password:
        return {"error": "Invalid credentials"}
    return {"token": generate_jwt_token(user)}


@app.post("/register")
async def register(credentials: UserCredentials, session: SessionDep):
    user = User.model_validate(credentials)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"token": generate_jwt_token(user)}

@app.post("/up/{fmt}/{name}")
async def upload(credentials: UserDependency,session: SessionDep,data: Annotated[str | bytes, Header()],fmt:str,name:str):
    fp = get_filepath(credentials.id,name)
    file = File(id=hash(f"files/{credentials.id}/{name}{fmt}"),filename=name,owner_id=credentials.id,uploaded_at=round(datetime.now(timezone.utc).timestamp()))
    session.add(file)
    await session.commit()
    await session.refresh(file)
    if fmt == "img":
        with open(fp, "wb") as f:
            f.write(base64.b64decode(data))
        return {"success": "Image saved successfully", "saved_to": fp}
    if fmt == "txt":
        with open(fp,"w") as f:
            f.write(base64.b64decode(data).decode())
        return {"success": "Text saved successfully", "saved_to": fp}
    else:
        return {"error": "Invalid format; Available formats: img, txt"}
    
@app.post("/del/{name}")
async def delete(credentials: UserDependency,session: SessionDep, name:str):
    result = await session.exec(select(File).where(File.filename==name))
    file = result.one()
    fp = get_existing_filepath(credentials.id,file.filename)
    await session.delete(file)
    await session.commit()
    os.remove(fp)
    
@app.get("/files/{id}/{file}")
async def get_file(id, file:str):
    with open(get_existing_filepath(id,file),'rb') as f:
        content = f.read()
        if file.endswith('.png'):
            return Response(content,media_type="image/png")
        else:
            return Response(content,media_type="text/plain")
        return content
    
@app.get("/embed/{id}/{file}")
async def get_file_embed(id:int,file:str):
    with open(get_existing_filepath(id,file),'rb') as f:
        content = f.read()
        if file.endswith('.png'):
            title = os.environ.get("EMBED_TITLE","File Sharing")
            
            cont = f"""
<html>
    <head>
        <meta property="og:title" content="{title}" />
        <meta property="og:image" content="/files/{id}/{file}" />
        <meta property="og:url" content="/" />
        <meta property="og:type" content="website" />
    </head>
    <body>
        Nothing to see here... maybe go to <a href="/docs">/docs?</a><br><br>
        Or view the file <a href="/files/{id}/{file}">here</a>.<br><br>
        Actually, Heres a preview: <img src="/files/{id}/{file}" alt="Preview not available">
    </body>
</html>
            """
            return Response(cont,media_type="text/html")
        else:
            title = os.environ.get("EMBED_TITLE","File Sharing")
            
            cont = f"""
<html>
    <head>
        <meta property="og:title" content="{title}" />
        <meta property="og:description" content="{content.decode()}" />
        <meta property="og:url" content="/" />
        <meta property="og:type" content="website" />
    </head>
    <body>
        Nothing to see here... maybe go to <a href="/docs">/docs?</a><br><br>
        Or view the file <a href="/files/{id}/{file}">here</a>.
    </body>
</html>
            """
            return Response(cont,media_type="text/html")
        return content
    
"""
HOW TO USE ALEMBIC:

TO CREATE A NEW TABLE:
    alembic revision --autogenerate -m "update_name"

THEN TO GO migrations/versions/someid_update_name.py AND ADD AN IMPORT FOR SQLMODEL

TO UPGRADE DATABASE:
    alembic upgrade head
"""
