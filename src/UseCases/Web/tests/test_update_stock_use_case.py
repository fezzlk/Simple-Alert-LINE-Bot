from datetime import datetime
from types import SimpleNamespace

import pytest
from werkzeug.exceptions import BadRequest
from werkzeug.datastructures import ImmutableMultiDict

from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Web.UpdateStockUseCase import UpdateStockUseCase


class DummyStockRepository(IStockRepository):
    def __init__(self):
        self.last_query = None
        self.last_values = None

    def create(self, new_stock):
        return new_stock

    def update(self, query, new_values) -> int:
        self.last_query = query
        self.last_values = new_values
        return 1

    def delete(self, query) -> int:
        return 0

    def find(self, query):
        return []


class DummyPageContents:
    def __init__(self, request, login_user):
        self.request = request
        self._login_user = login_user

    def get(self, key):
        if key == "login_user":
            return self._login_user
        return None


def test_update_stock_missing_stock_id():
    repo = DummyStockRepository()
    use_case = UpdateStockUseCase(stock_repository=repo)
    req = SimpleNamespace(form=ImmutableMultiDict({}))
    page_contents = DummyPageContents(
        request=req,
        login_user=WebUser(web_user_name="u", web_user_email="u@example.com"),
    )

    with pytest.raises(BadRequest):
        use_case.execute(page_contents=page_contents)


def test_update_stock_updates_fields_and_query():
    repo = DummyStockRepository()
    use_case = UpdateStockUseCase(stock_repository=repo)
    stock_id = "507f1f77bcf86cd799439011"
    req = SimpleNamespace(
        form=ImmutableMultiDict(
            {
                "stock_id": stock_id,
                "item_name": "rice",
                "str_expiry_date": "2025-01-02",
                "str_created_at": "2025-01-01",
            }
        )
    )
    login_user = WebUser(
        _id="W1",
        web_user_name="u",
        web_user_email="u@example.com",
        linked_line_user_id="L1",
        is_linked_line_user=True,
    )
    page_contents = DummyPageContents(request=req, login_user=login_user)

    use_case.execute(page_contents=page_contents)

    assert isinstance(repo.last_query["_id"], str)
    assert repo.last_query["_id"] == stock_id
    assert repo.last_query["owner_id__in"] == ["W1", "L1"]
    assert repo.last_values["item_name"] == "rice"
    assert repo.last_values["expiry_date"] == datetime(2025, 1, 2)
    assert repo.last_values["created_at"] == datetime(2025, 1, 1)
