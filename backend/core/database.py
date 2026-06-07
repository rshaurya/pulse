from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# manages the connection pool to PostgreSQL.
# echo=True prints the generated SQL to terminal to see how SQLModel works
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# 2. The Dependency: This is what FastAPI endpoints will use to talk to the DB.
async def get_session() -> AsyncSession:
    """
    Provides a transactional scope around a series of operations.
    It yields a database session to the API endpoint, and automatically 
    closes/returns the connection when the endpoint finishes.
    """
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session  
        # When the API endpoint is done, it resumes here and safely closes the session.