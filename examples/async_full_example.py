import asyncio

from spilli_dbal.dbal import AsyncSqlaDBAL
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException
from spilli_dbal.models.base import ModelMixin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

engine = create_async_engine('sqlite+aiosqlite://', echo=False)
Base = declarative_base()


class Items(ModelMixin, Base):
    __tablename__ = 'items'
    data: Mapped[str] = mapped_column(comment='Data of item.')


class ItemsDBAL(AsyncSqlaDBAL[Items]):
    """Items DBAL."""


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        new_item = await ItemsDBAL(session).create(data='data')
        print('=>', 'New item:', new_item)

        item = await ItemsDBAL(session).read(id=new_item.id)
        print('=>', 'Item:', item)

        updated_item = await ItemsDBAL(session).update(id=new_item.id, data='updated_data')
        print('=>', 'Updated item:', updated_item)

        await ItemsDBAL(session).delete(id=new_item.id)
        try:
            await ItemsDBAL(session).read(id=new_item.id)
        except DBALObjectNotFoundException:
            print('=>', 'Deleted item.')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
