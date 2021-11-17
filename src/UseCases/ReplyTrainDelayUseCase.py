from src.services import (
    train_service,
    line_response_service,
)


class ReplyTrainDelayUseCase:
    def execute(self) -> None:
        print('get train info')
        data = train_service.get_trains_delay_info()
        res = '運行情報\n'
        for name, info in data.items():
            res += '\n' + name + ':\n' + info + '\n'
        line_response_service.add_message(res)
