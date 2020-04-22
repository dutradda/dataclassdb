import pytest

from dbdaora import SortedSetEntity, SortedSetRepository


class FakeRepository(SortedSetRepository[str]):
    entity_name = 'fake'
    key_attrs = ('id',)


@pytest.fixture
def fake_entity():
    return SortedSetEntity(id='fake', data=['1', '2'])


@pytest.fixture
def fake_entity_withscores():
    return SortedSetEntity(id='fake', data=[('1', 0), ('2', 1)])


@pytest.fixture
def dict_repository_cls():
    return FakeRepository