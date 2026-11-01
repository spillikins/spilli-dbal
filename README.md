# Spilli-DBAL

Web-framework independent CRUD tools for working with database via SQLAlchemy.

<!--TOC-->

- [Spilli-DBAL](#spilli-dbal)
  - [Features](#features)
  - [Installation](#installation)
  - [Examples](#examples)
    - [Async example](#async-example)
  - [Project automation](#project-automation)

<!--TOC-->

## Features

* DBAL - database access layer.
* CRUD methods for create, read, update and delete object from database.
* Bulk methods for create, read, update and delete object from database.
* Method of paginating data.
* StatementMaker class for create query 'per-one-model'.
* [Marshmallow](https://github.com/marshmallow-code/marshmallow) schemas for serialization input data for StatementMaker.
* [Marshmallow](https://github.com/marshmallow-code/marshmallow) schemas for deserialization StatementMaker result object to `dict`.
* Datetime with UTC timezone validation in `BaseSchema`.
* Support for both synchronous and asynchronous (async/await) database operations.


## Installation

Recommended using the latest version of Python. Spilli-DBAL supports Python 3.12 and newer.

Install and update using `pip`:

```shell
$ pip install -U spilli_dbal
```

## Examples

### Async example

```python
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
```

Other examples in `example/` folder.

## Project automation

All commands are defined in the `Makefile`.

Builds the package, installs it from the sdist, and installs pre-commit hooks into git
```shell
make install
```

Run for build, install and test project.
```shell
make all
```
