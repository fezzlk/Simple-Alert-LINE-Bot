from src.Domains.Entities.Stock import Stock
from src.Infrastructure.Repositories.StockRepository import StockRepository
from src.tests.dummies import generate_dummy_stock_list


def test_success():
    # Arrange
    stock_repository = StockRepository()
    dummy_stocks = generate_dummy_stock_list()[:3]
    for dummy_stock in dummy_stocks:
        stock_repository.create(
            new_stock=dummy_stock,
        )
    target_stocks = dummy_stocks[:1]
    query = {
        'item_name': target_stocks[0].item_name,
    }

    # Act
    result = stock_repository.find(query=query)

    # Assert
    assert len(result) == len(target_stocks)
    for i in range(len(result)):
        assert isinstance(result[i], Stock)
        assert result[i].item_name == target_stocks[i].item_name
        assert result[i].owner_id == target_stocks[i].owner_id
        assert result[i].expiry_date == target_stocks[i].expiry_date
        assert result[i].status == target_stocks[i].status


def test_success_hit_all_records():
    # Arrange
    stock_repository = StockRepository()
    dummy_stocks = generate_dummy_stock_list()[:3]
    for dummy_stock in dummy_stocks:
        stock_repository.create(
            new_stock=dummy_stock,
        )

    # Act
    result = stock_repository.find()

    # Assert
    assert len(result) == len(dummy_stocks)
    for i in range(len(result)):
        assert isinstance(result[i], Stock)
        assert result[i].item_name == dummy_stocks[i].item_name
        assert result[i].owner_id == dummy_stocks[i].owner_id
        assert result[i].expiry_date == dummy_stocks[i].expiry_date
        assert result[i].status == dummy_stocks[i].status
