import pytest
from datetime import datetime
import werkzeug
from typing import Tuple
from flask import session, request
from src.UseCases.Web.AddStockUseCase import AddStockUseCase
from src.models.PageContents import PageContents
from src.Infrastructure.Repositories.StockRepository import StockRepository
from src.Domains.Entities.WebUser import WebUser
from src.Domains.Entities.Stock import Stock


dummy_web_user = WebUser(
    _id='U0123456789abcdefghijklmnopqrstu1',
    web_user_name='dummy_web_user_1',
    web_user_email='dummy1@example.com',
)


dummy_stocks = [
    Stock(
        item_name='dummy_good_1',
        owner_id='U0123456789abcdefghijklmnopqrstu1',
        expiry_date=None,
        status=1,
    ),
    Stock(
        item_name='dummy_good_2',
        owner_id='U0123456789abcdefghijklmnopqrstu1',
        expiry_date=datetime(2022, 1, 1),
        status=1,
    ),
]


@pytest.fixture(params=[
    # (req_stock_name, req_stock_expiry_date, index_of_expected_dummy_stock)
    ('dummy_good_1', '', 0),
    ('dummy_good_2', '2022-01-01', 1),
])
def case(request) -> Tuple[str, datetime, int]:
    return request.param


def test_success(dummy_app, case):
    with dummy_app.test_request_context():
        # Arrange
        stock_repository = StockRepository()
        use_case = AddStockUseCase(stock_repository=stock_repository)
        session['login_user'] = dummy_web_user

        request.form = werkzeug.datastructures.ImmutableMultiDict({
            'item_name': case[0],
            'expiry_date': case[1],
        })

        page_contents = PageContents(session, request)

        expected_stocks = dummy_stocks

        # Act
        result = use_case.execute(page_contents=page_contents)

        # Assert
        assert result == case[0]

        data = stock_repository.find()
        for i in range(len(data)):
            assert data[i].item_name == dummy_stocks[case[2]].item_name
            assert data[i].expiry_date == dummy_stocks[case[2]].expiry_date
