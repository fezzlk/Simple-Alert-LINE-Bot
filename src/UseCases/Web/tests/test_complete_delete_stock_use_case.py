from types import SimpleNamespace

import pytest
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.datastructures import ImmutableMultiDict

from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Web.CompleteDeleteStockUseCase import CompleteDeleteStockUseCase


class DummyStockRepository(IStockRepository):
    def __init__(self, delete_result: int):
        self.delete_result = delete_result
        self.last_query = None

    def create(self, new_stock):
        return new_stock

    def update(self, query, new_values) -> int:
        return 0

    def delete(self, query) -> int:
        self.last_query = query
        return self.delete_result

    def find(self, query):
        return []


class DummyPageContents:
    def __init__(self, request):
        self.request = request


def test_complete_delete_missing_id():
    repo = DummyStockRepository(delete_result=1)
    use_case = CompleteDeleteStockUseCase(stock_repository=repo)
    page_contents = DummyPageContents(request=SimpleNamespace(form=ImmutableMultiDict({})))

    with pytest.raises(BadRequest):
        use_case.execute(page_contents=page_contents)


def test_complete_delete_not_found():
    repo = DummyStockRepository(delete_result=0)
    use_case = CompleteDeleteStockUseCase(stock_repository=repo)
    page_contents = DummyPageContents(
        request=SimpleNamespace(form=ImmutableMultiDict({"stock_id": "507f1f77bcf86cd799439011"}))
    )

    with pytest.raises(NotFound):
        use_case.execute(page_contents=page_contents)


def test_complete_delete_success():
    repo = DummyStockRepository(delete_result=1)
    use_case = CompleteDeleteStockUseCase(stock_repository=repo)
    stock_id = "507f1f77bcf86cd799439011"
    page_contents = DummyPageContents(
        request=SimpleNamespace(form=ImmutableMultiDict({"stock_id": stock_id}))
    )

    use_case.execute(page_contents=page_contents)

    assert isinstance(repo.last_query["_id"], str)
