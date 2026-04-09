import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

engine = sa_async.create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=sa_async.AsyncSession,
)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
