# Spilli-DBAL

Web-framework independent CRUD tools for working with database via SQLAlchemy.

<!--TOC-->

- [Spilli-DBAL](#spilli-dbal)
  - [Features](#features)
  - [Installation](#installation)
  - [Examples](#examples)
    - [Full example](#full-example)
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

## Installation

Recommended using the latest version of Python. Spilli-DBAL supports Python 3.12 and newer.

Install and update using `pip`:

```shell
$ pip install -U spilli_dbal
```

## Examples

### Full example

```python
from spilli_dbal.models.base import ModelMixin
from spilli_dbal.dbal import SqlaDBAL
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException
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
```

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
