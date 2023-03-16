from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession 
from sqlalchemy.orm.session import sessionmaker


DSN = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5430/asyncio_hw'
engine = create_async_engine(DSN)

Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)