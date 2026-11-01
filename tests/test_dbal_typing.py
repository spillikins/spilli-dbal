import pytest
from spilli_dbal.dbal import AsyncSqlaDBAL
from spilli_dbal.dbal import SqlaDBAL

BASE_CLASSES = [SqlaDBAL, AsyncSqlaDBAL]


@pytest.mark.parametrize('base_class', BASE_CLASSES)
def test_dbal__subclass_inherits_model(fx_table_models, base_class):
    Parents, _, _ = fx_table_models

    class ParentsDBAL(base_class[Parents]):
        """Parents DBAL."""

    class ParentsChildDBAL(ParentsDBAL):
        """Child DBAL."""

    assert ParentsChildDBAL._model is Parents


@pytest.mark.parametrize('base_class', BASE_CLASSES)
def test_dbal__subclass_without_model_error(base_class):
    with pytest.raises(TypeError) as e:

        class BrokenDBAL(base_class):
            """Broken DBAL."""

    assert e.value.args[0] == '<BrokenDBAL> must be created as SqlaDBAL[Model] subclass.'


@pytest.mark.parametrize('base_class', BASE_CLASSES)
def test_dbal__subclass_multiple_inheritance(fx_table_models, base_class):
    Parents, _, _ = fx_table_models

    class Extra:
        """Extra mixin."""

    class MixedDBAL(Extra, base_class[Parents]):
        """Mixed DBAL."""

    assert MixedDBAL._model is Parents
