from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///uploader.db", echo=True, future=True)


# This is now handled using alembic migrations
# async def init_db():
#     async with engine.begin() as conn:
#         # await conn.run_sync(SQLModel.metadata.drop_all)
#         await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        
async def get_files_by_user(owner_id):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        from sqlmodel import select
        statement = select(File).where(File.owner_id == owner_id)
        result = await session.execute(statement)
        return result.scalars().all()


class UserCredentials(SQLModel):
    username: str = Field(unique=True)
    password: str


class User(UserCredentials, table=True):
    id: int = Field(default=None, primary_key=True)


class File(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    filename: str
    owner_id: int = Field(foreign_key="user.id")
    uploaded_at: int = Field(
        default_factory=lambda: datetime.now(timezone.utc).timestamp()
    )


SessionDep = Annotated[AsyncSession, Depends(get_session)]
