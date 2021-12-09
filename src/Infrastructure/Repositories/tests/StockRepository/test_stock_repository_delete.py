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
    other_stocks = dummy_stocks[1:]
    query = {
        'item_name': target_stocks[0].item_name,
    }

    # Act
    result = stock_repository.delete(query=query)

    # Assert
    assert result == len(target_stocks)
    records_in_db = stock_repository.find()
    assert len(records_in_db) == len(other_stocks)
    for i in range(len(records_in_db)):
        assert records_in_db[i].item_name == other_stocks[i].item_name
        assert records_in_db[i].owner_id == other_stocks[i].owner_id
        assert records_in_db[i].expiry_date == other_stocks[i].expiry_date
        assert records_in_db[i].status == other_stocks[i].status


def test_success_hit_all_records():
    # Arrange
    stock_repository = StockRepository()
    dummy_stocks = generate_dummy_stock_list()[:3]
    for dummy_stock in dummy_stocks:
        stock_repository.create(
            new_stock=dummy_stock,
        )

    # Act
    result = stock_repository.delete()

    # Assert
    assert result == len(dummy_stocks)
    records_in_db = stock_repository.find()
    assert len(records_in_db) == 0
