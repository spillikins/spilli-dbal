import pytest
from spilli_dbal.dbal import SqlaDBAL


def test_dbal__subclass_inherits_model(fx_parent_dbal):
    class ParentsChildDBAL(fx_parent_dbal):
        """Child DBAL."""

    assert ParentsChildDBAL._model is fx_parent_dbal._model


def test_dbal__subclass_without_model_error():
    with pytest.raises(TypeError) as e:

        class BrokenDBAL(SqlaDBAL):
            """Broken DBAL."""

    assert e.value.args[0] == '<BrokenDBAL> must be created as SqlaDBAL[Model] subclass.'


def test_dbal__subclass_multiple_inheritance(fx_db):
    _, Parents, _, _ = fx_db

    class Extra:
        """Extra mixin."""

    class MixedDBAL(Extra, SqlaDBAL[Parents]):
        """Mixed DBAL."""

    assert MixedDBAL._model is Parents
