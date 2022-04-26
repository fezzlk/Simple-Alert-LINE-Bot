from typing import List
from flask import session, request
from src.UseCases.Web.ViewDeletedStockListUseCase import ViewDeletedStockListUseCase
from src.models.PageContents import PageContents, StockListData
from src.Infrastructure.Repositories.StockRepository import StockRepository
from src.Domains.Entities.WebUser import WebUser
from src.Domains.Entities.Stock import Stock
from datetime import datetime
from src.models.StockViewModel import StockViewModel


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
            created_at=datetime(2020, 1, 1),
            status=2,
        ),
        Stock(
            item_name='dummy_good_2',
            owner_id='U0123456789abcdefghijklmnopqrstu1',
            expiry_date=datetime(2020, 2, 2),
            created_at=datetime(2020, 2, 2),
            status=2,
        ),
        Stock(
            item_name='dummy_good_3',
            owner_id='U0123456789abcdefghijklmnopqrstu1',
            expiry_date=datetime(2020, 3, 3),
            created_at=datetime(2020, 3, 3),
            status=1,
        ),
        Stock(
            item_name='dummy_good_4',
            owner_id='U0123456789abcdefghijklmnopqrstu2',
            expiry_date=datetime(2020, 4, 4),
            created_at=datetime(2020, 4, 4),
            status=2,
        ),
    ]


def generate_expected_stock_list() -> List[StockViewModel]:
    return [
        StockViewModel(
            item_name='dummy_good_1',
            str_expiry_date='',
            str_created_at='2020/01/01',
        ),
        StockViewModel(
            item_name='dummy_good_2',
            str_expiry_date='2020/02/02',
            str_created_at='2020/02/02',
        ),
    ]


def test_success(dummy_app):
    with dummy_app.test_request_context():
        # Arrange
        use_case = ViewDeletedStockListUseCase()
        session['login_user'] = generate_dummy_web_user_list()[0]
        page_contents = PageContents[StockListData](
            session, request, StockListData)

        stock_repository = StockRepository()
        dummy_stocks = generate_dummy_stock_list()

        for dummy_stock in dummy_stocks:
            stock_repository.create(
                new_stock=dummy_stock,
            )
        expected_stocks = generate_expected_stock_list()

        expected_keys = [
            'item_name',
            'str_created_at',
            'str_expiry_date',
        ]
        expected_labels = ['名前', '登録日', '期限']

        # Act
        page_contents = use_case.execute(page_contents=page_contents)

        # Assert
        assert isinstance(page_contents, PageContents)
        assert page_contents.page_title == '削除済みストック一覧'
        for i in range(len(expected_keys)):
            assert page_contents.data.keys[i] == expected_keys[i]
        for i in range(len(expected_labels)):
            assert page_contents.data.labels[i] == expected_labels[i]

        for i in range(len(expected_stocks)):
            assert isinstance(page_contents.data.stocks[i], StockViewModel)
            assert page_contents.data.stocks[i].item_name == expected_stocks[i].item_name
            assert page_contents.data.stocks[i].str_expiry_date == expected_stocks[i].str_expiry_date
            assert page_contents.data.stocks[i].str_expiry_date == expected_stocks[i].str_expiry_date
