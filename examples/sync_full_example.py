from spilli_dbal.dbal import SqlaDBAL
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException
from spilli_dbal.models.base import ModelMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Session

engine = create_engine('sqlite://', echo=True, future=True)
session = Session(engine)
Base = declarative_base()


class Items(ModelMixin, Base):
    __tablename__ = 'items'
    data: Mapped[str] = mapped_column(comment='Data of item.')


Base.metadata.create_all(engine)


class ItemsDBAL(SqlaDBAL[Items]):
    """Items DBAL."""


if __name__ == '__main__':
    new_item = ItemsDBAL(session).create(data='data')
    print('=>', 'New item:', new_item)

    item = ItemsDBAL(session).read(id=new_item.id)
    print('=>', 'Item:', item)

    updated_item = ItemsDBAL(session).update(id=new_item.id, data='updated_data')
    print('=>', 'Updated item:', updated_item)

    ItemsDBAL(session).delete(id=new_item.id)
    try:
        ItemsDBAL(session).read(id=new_item.id)
    except DBALObjectNotFoundException:
        print('=>', 'Deleted item.')
