from types import SimpleNamespace

import pytest
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.datastructures import ImmutableMultiDict

from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Web.RestoreStockUseCase import RestoreStockUseCase


class DummyStockRepository(IStockRepository):
    def __init__(self, update_result: int):
        self.update_result = update_result
        self.last_query = None
        self.last_values = None

    def create(self, new_stock):
        return new_stock

    def update(self, query, new_values) -> int:
        self.last_query = query
        self.last_values = new_values
        return self.update_result

    def delete(self, query) -> int:
        return 0

    def find(self, query):
        return []


class DummyPageContents:
    def __init__(self, request):
        self.request = request


def test_restore_stock_missing_id():
    repo = DummyStockRepository(update_result=1)
    use_case = RestoreStockUseCase(stock_repository=repo)
    page_contents = DummyPageContents(request=SimpleNamespace(form=ImmutableMultiDict({})))

    with pytest.raises(BadRequest):
        use_case.execute(page_contents=page_contents)


def test_restore_stock_not_found():
    repo = DummyStockRepository(update_result=0)
    use_case = RestoreStockUseCase(stock_repository=repo)
    page_contents = DummyPageContents(
        request=SimpleNamespace(form=ImmutableMultiDict({"stock_id": "507f1f77bcf86cd799439011"}))
    )

    with pytest.raises(NotFound):
        use_case.execute(page_contents=page_contents)


def test_restore_stock_success():
    repo = DummyStockRepository(update_result=1)
    use_case = RestoreStockUseCase(stock_repository=repo)
    stock_id = "507f1f77bcf86cd799439011"
    page_contents = DummyPageContents(
        request=SimpleNamespace(form=ImmutableMultiDict({"stock_id": stock_id}))
    )

    use_case.execute(page_contents=page_contents)

    assert isinstance(repo.last_query["_id"], str)
    assert repo.last_values == {"status": 1}
