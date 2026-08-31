from typing import Any
from typing import get_args
from typing import Literal
from typing import TypeVar

from spilli_dbal.dbal.exceptions import DBALColumnNonExistException
from spilli_dbal.dbal.exceptions import DBALCreateException
from spilli_dbal.dbal.exceptions import DBALForeignKeyConstraintFailedException
from spilli_dbal.dbal.exceptions import DBALNotNullConstraintFailedException
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException
from spilli_dbal.dbal.exceptions import DBALUnexpectedValueTypeException
from spilli_dbal.dbal.exceptions import DBALUpdateException
from spilli_dbal.dbal.paginate import PageMixin
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy import Sequence
from sqlalchemy import update
from sqlalchemy.exc import CompileError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError


def compile_error_handler(e: CompileError) -> None:
    if e.args[0].startswith('Unconsumed column names:'):
        raise DBALColumnNonExistException(e)


def integrity_error_handler(e: IntegrityError, s: Session) -> None:
    db_type = s.get_bind().name

    if db_type == 'sqlite':
        if e.orig.sqlite_errorname == 'SQLITE_CONSTRAINT_NOTNULL':
            raise DBALNotNullConstraintFailedException(e.orig.args[0])
        if e.orig.sqlite_errorname == 'SQLITE_CONSTRAINT_FOREIGNKEY':
            raise DBALForeignKeyConstraintFailedException(e.orig.args[0])

    elif db_type == 'postgresql':
        if 'is not present in table' in e.orig.diag.message_detail:
            raise DBALForeignKeyConstraintFailedException(e.orig.diag.message_detail)

    else:
        raise NotImplementedError(f'DB <{db_type}> not implemented.')


class SqlaDBAL[M](PageMixin):
    """Base SqlaDBAL, implement base CRUD sqlalchemy operations."""

    _model: type[M]

    def __init_subclass__(cls) -> None:
        for base in cls.__orig_bases__:
            args = get_args(base)
            if args and not isinstance(args[0], TypeVar):
                cls._model = args[0]
                break
        else:
            if not hasattr(cls, '_model'):
                raise TypeError(f'<{cls.__name__}> must be created as SqlaDBAL[Model] subclass.')

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **kwargs) -> M:
        try:
            new_obj = self._model(**kwargs)
        except TypeError as e:
            raise DBALUnexpectedValueTypeException(e)

        self._session.add(new_obj)

        try:
            self._session.commit()

        except CompileError as e:
            self._session.rollback()
            compile_error_handler(e)
            raise DBALCreateException(e)

        except IntegrityError as e:
            self._session.rollback()
            integrity_error_handler(e, self._session)
            raise DBALCreateException(e)

        except ProgrammingError as e:
            self._session.rollback()
            raise DBALUnexpectedValueTypeException(e)

        except Exception as e:
            self._session.rollback()
            raise DBALCreateException(e)

        return new_obj

    def bulk_create(self, data: list[dict]) -> Result[Any]:
        try:
            new_objects = self._session.execute(insert(self._model), data)
        except (IntegrityError, ProgrammingError) as e:
            raise DBALCreateException(e)

        return new_objects

    def read(self, id: Any) -> M:
        stmt = select(self._model).where(self._model.id == id)

        try:
            return self._session.scalars(stmt).one()
        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)

    def bulk_read(self, ids: list[Any]) -> Sequence[M]:
        return self.read_filtered_list(id=ids)

    def read_all(self) -> Sequence[M]:
        stmt = select(self._model)
        return self._session.scalars(stmt).all()

    def read_filtered(self, **kwargs) -> M:
        filters = [getattr(self._model, k) == v for k, v in kwargs.items()]
        stmt = select(self._model).where(*filters)

        try:
            return self._session.scalars(stmt).one()
        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)

    def read_filtered_list(
        self, sort_order: Literal['asc', 'desc'] = 'asc', sort_field: str | None = None, **kwargs
    ) -> Sequence[M]:
        filters = []
        for k, v in kwargs.items():
            if isinstance(v, list):
                filters.append(getattr(self._model, k).in_(v))
            else:
                filters.append(getattr(self._model, k) == v)

        stmt = select(self._model).where(*filters)

        if sort_field:
            if sort_order == 'desc':
                order_column = getattr(self._model, sort_field).desc()
            else:
                order_column = getattr(self._model, sort_field)
            stmt = stmt.order_by(order_column)

        return self._session.scalars(stmt).all()

    def update(self, id: Any, **data) -> M:
        stmt = update(self._model).where(self._model.id == id).values(**data).returning(self._model)

        try:
            obj = self._session.scalars(stmt).one()

        except CompileError as e:
            compile_error_handler(e)
            raise DBALUpdateException(e)

        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)

        except IntegrityError as e:
            self._session.rollback()
            integrity_error_handler(e, self._session)
            raise DBALUpdateException(e)

        except ProgrammingError as e:
            self._session.rollback()
            raise DBALUnexpectedValueTypeException(e)

        except Exception as e:
            self._session.rollback()
            raise DBALUpdateException(e)

        return obj

    def bulk_update(self, data: list[dict]) -> None:
        try:
            self._session.execute(update(self._model), data)
        except ProgrammingError as e:
            raise DBALUpdateException(e)
        except StaleDataError as e:
            raise DBALObjectNotFoundException(e)

    def delete(self, id: Any) -> None:
        self._session.execute(delete(self._model).where(self._model.id == id))
        self._session.commit()

    def bulk_delete(self, ids: list[Any]) -> None:
        self._session.execute(delete(self._model).where(self._model.id.in_(ids)))
        self._session.commit()
