import werkzeug
from typing import List
from flask import session, request
from src.UseCases.Web.AddStockUseCase import AddStockUseCase
from src.models.PageContents import PageContents
from src.Infrastructure.Repositories.StockRepository import StockRepository
from src.Domains.Entities.WebUser import WebUser
from src.Domains.Entities.Stock import Stock


def generate_dummy_web_user_list() -> List[WebUser]:
    return [
        WebUser(
            _id='U0123456789abcdefghijklmnopqrstu1',
            web_user_name='dummy_web_user_1',
            web_user_email='dummy1@example.com',
        ),
    ]


def generate_dummy_stock_list() -> List[Stock]:
    return [
        Stock(
            item_name='dummy_good_1',
            owner_id='U0123456789abcdefghijklmnopqrstu1',
            expiry_date=None,
            status=1,
        ),
    ]


def test_success(dummy_app):
    with dummy_app.test_request_context():
        # Arrange
        use_case = AddStockUseCase()
        session['login_user'] = generate_dummy_web_user_list()[0]

        request.form = werkzeug.datastructures.ImmutableMultiDict({
            'expiry_date': '',
            'item_name': 'dummy_good_1',
        })

        page_contents = PageContents(session, request)

        expected_stocks = generate_dummy_stock_list()

        # Act
        result = use_case.execute(page_contents=page_contents)

        # Assert
        assert result == 'dummy_good_1'

        data = StockRepository().find()
        for i in range(len(data)):
            assert data[i].item_name == expected_stocks[i].item_name
            assert data[i].expiry_date == expected_stocks[i].expiry_date
