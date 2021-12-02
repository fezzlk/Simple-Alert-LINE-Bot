from src.Infrastructure.Repositories.StockRepository import StockRepository
from src.tests.dummies import generate_dummy_stock_list


def test_success():
    # Arrange
    stock_repository = StockRepository()
    dummy_stocks = generate_dummy_stock_list()[:3]
    for dummy_stock in dummy_stocks:
        result = stock_repository.create(
            new_stock=dummy_stock
        )
    target_stock = dummy_stocks[0]
    query = {
        'goods_name': target_stock.goods_name,
    }
    new_values = {
        'owner_line_id': 'updated'
    }

    # Act
    result = stock_repository.update(
        query=query,
        new_values=new_values,
    )

    # Assert
    assert result == 1
    records_in_db = stock_repository.find(query=query)
    for record in records_in_db:
        assert record.goods_name == target_stock.goods_name
        assert record.owner_line_id == new_values['owner_line_id']
