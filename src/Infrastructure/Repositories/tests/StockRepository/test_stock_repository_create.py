from src.Domains.Entities.Stock import Stock
from src.Infrastructure.Repositories.StockRepository import StockRepository
from src.tests.dummies import generate_dummy_stock_list


def test_success():
    # Arrange
    stock_repository = StockRepository()
    dummy_stock = generate_dummy_stock_list()[0]

    # Act
    result = stock_repository.create(
        new_stock=dummy_stock,
    )

    # Assert
    assert isinstance(result, Stock)
    assert result.goods_name == dummy_stock.goods_name
    assert result.owner_id == dummy_stock.owner_id
    assert result.expiry_date == dummy_stock.expiry_date
    assert result.status == dummy_stock.status
