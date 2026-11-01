from collections.abc import Sequence
from typing import Any
from typing import get_args
from typing import Literal
from typing import TypeVar

from spilli_dbal.dbal.exceptions import DBALColumnNonExistException
from spilli_dbal.dbal.exceptions import DBALCreateException
from spilli_dbal.dbal.exceptions import DBALForeignKeyConstraintFailedException
from spilli_dbal.dbal.exceptions import DBALMultipleResultsFoundException
from spilli_dbal.dbal.exceptions import DBALNotNullConstraintFailedException
from spilli_dbal.dbal.exceptions import DBALObjectNotFoundException
from spilli_dbal.dbal.exceptions import DBALUnexpectedValueTypeException
from spilli_dbal.dbal.exceptions import DBALUpdateException
from spilli_dbal.dbal.paginate import PageMixin
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import CompileError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError


def compile_error_handler(e: CompileError) -> None:
    if e.args and e.args[0].startswith('Unconsumed column names:'):
        raise DBALColumnNonExistException(e)
    else:
        raise NotImplementedError(f'DBAL <{e.args[0] if e.args else e}> not implemented.')


def integrity_error_handler(e: IntegrityError, s: Session | AsyncSession) -> None:
    bind = s.get_bind()
    db_type = bind.name if bind is not None else None

    if db_type == 'sqlite':
        if hasattr(e.orig, 'sqlite_errorname'):
            if e.orig.sqlite_errorname == 'SQLITE_CONSTRAINT_NOTNULL':
                raise DBALNotNullConstraintFailedException(e.orig.args[0])
            if e.orig.sqlite_errorname == 'SQLITE_CONSTRAINT_FOREIGNKEY':
                raise DBALForeignKeyConstraintFailedException(e.orig.args[0])
        if e.orig and e.orig.args:
            msg = e.orig.args[0]
            raise DBALCreateException(msg)

    elif db_type == 'postgresql':
        if hasattr(e.orig, 'diag') and e.orig.diag and hasattr(e.orig.diag, 'message_detail'):
            if 'is not present in table' in e.orig.diag.message_detail:
                raise DBALForeignKeyConstraintFailedException(e.orig.diag.message_detail)
        if 'is not present in table' in str(e.orig):
            raise DBALForeignKeyConstraintFailedException(str(e.orig))
        if e.orig and e.orig.args:
            raise DBALCreateException(e.orig.args[0])

    else:
        raise NotImplementedError(f'DB <{db_type}> not implemented.')


class SqlaDBALBase[M]:
    """Base class for SQLAlchemy DBAL implementations."""

    _model: type[M]

    def __init_subclass__(cls) -> None:
        if cls is SqlaDBALBase or getattr(cls, '__name__', '') in ('SqlaDBAL', 'AsyncSqlaDBAL'):
            super().__init_subclass__()
            return
        if hasattr(cls, '__orig_bases__'):
            for base in cls.__orig_bases__:
                args = get_args(base)
                if args and not isinstance(args[0], TypeVar):
                    cls._model = args[0]
                    break
            else:
                if not hasattr(cls, '_model'):
                    raise TypeError(
                        f'<{cls.__name__}> must be created as SqlaDBAL[Model] subclass.'
                    )
        else:
            if not hasattr(cls, '_model'):
                raise TypeError(f'<{cls.__name__}> must be created as SqlaDBAL[Model] subclass.')
        super().__init_subclass__()

    def _make_instance(self, **kwargs) -> M:
        try:
            return self._model(**kwargs)
        except TypeError as e:
            raise DBALUnexpectedValueTypeException(e)

    def _build_filters(self, **kwargs) -> list[Any]:
        filters = []
        for k, v in kwargs.items():
            if isinstance(v, list):
                filters.append(getattr(self._model, k).in_(v))
            else:
                filters.append(getattr(self._model, k) == v)
        return filters

    def _stmt_read_by_id(self, id: Any):
        return select(self._model).where(self._model.id == id)

    def _stmt_read_all(self):
        return select(self._model)

    def _stmt_read_filtered(self, **kwargs):
        return select(self._model).where(*self._build_filters(**kwargs))

    def _stmt_read_filtered_list(
        self, sort_order: Literal['asc', 'desc'] = 'asc', sort_field: str | None = None, **kwargs
    ):
        stmt = select(self._model).where(*self._build_filters(**kwargs))
        if sort_field:
            col = getattr(self._model, sort_field)
            if sort_order == 'desc':
                stmt = stmt.order_by(col.desc())
            else:
                stmt = stmt.order_by(col)
        return stmt

    def _stmt_update(self, id: Any, **data):
        return update(self._model).where(self._model.id == id).values(**data).returning(self._model)

    def _stmt_delete(self, id: Any):
        return delete(self._model).where(self._model.id == id)

    def _stmt_bulk_delete(self, ids: list[Any]):
        return delete(self._model).where(self._model.id.in_(ids))

    def _stmt_bulk_insert(self):
        return insert(self._model)


class SqlaDBAL[M](SqlaDBALBase[M], PageMixin):
    """Base SqlaDBAL, implement base CRUD sqlalchemy operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **kwargs) -> M:
        new_obj = self._make_instance(**kwargs)

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
            new_objects = self._session.execute(self._stmt_bulk_insert(), data)
        except (IntegrityError, ProgrammingError) as e:
            raise DBALCreateException(e)

        return new_objects

    def read(self, id: Any) -> M:
        try:
            return self._session.scalars(self._stmt_read_by_id(id)).one()
        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)

    def bulk_read(self, ids: list[Any]) -> Sequence[M]:
        return self.read_filtered_list(id=ids)

    def read_all(self) -> Sequence[M]:
        return self._session.scalars(self._stmt_read_all()).all()

    def read_filtered(self, **kwargs) -> M:
        try:
            return self._session.scalars(self._stmt_read_filtered(**kwargs)).one()
        except NoResultFound as e:
            raise DBALObjectNotFoundException(e)
        except MultipleResultsFound as e:
            raise DBALMultipleResultsFoundException(e)

    def read_filtered_list(
        self, sort_order: Literal['asc', 'desc'] = 'asc', sort_field: str | None = None, **kwargs
    ) -> Sequence[M]:
        stmt = self._stmt_read_filtered_list(sort_order=sort_order, sort_field=sort_field, **kwargs)
        return self._session.scalars(stmt).all()

    def update(self, id: Any, **data) -> M:
        try:
            obj = self._session.scalars(self._stmt_update(id, **data)).one()

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
        self._session.execute(self._stmt_delete(id))

    def bulk_delete(self, ids: list[Any]) -> None:
        self._session.execute(self._stmt_bulk_delete(ids))
