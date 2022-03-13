from src.UseCases.Web.ViewStockListUseCase import ViewStockListUseCase


def test_success():
    # Arrange
    use_case = ViewStockListUseCase()

    # Act
    use_case.execute()

    # Assert
