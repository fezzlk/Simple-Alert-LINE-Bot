from datetime import datetime
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


def _days_left(expiry_date: datetime) -> int:
    return (expiry_date.date() - datetime.now().date()).days


def _expiry_label(expiry_date: datetime) -> str:
    days = _days_left(expiry_date)
    date_str = expiry_date.strftime("%-m/%-d")
    if days < 0:
        return f'{date_str}（{abs(days)}日超過）'
    if days == 0:
        return f'{date_str}（今日まで）'
    if days == 1:
        return f'{date_str}（明日まで）'
    return f'{date_str}（残り{days}日）'


def _urgency_icon(expiry_date: datetime) -> str:
    days = _days_left(expiry_date)
    if days < 0:
        return '🔴'
    if days <= 3:
        return '🟠'
    if days <= 7:
        return '🟡'
    return '🟢'


class ReplyStockUseCase(IUseCase):
    def __init__(
        self,
        stock_repository: IStockRepository,
        web_user_repository: IWebUserRepository,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
    ):
        self._stock_repository = stock_repository
        self._web_user_repository = web_user_repository
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service

    def execute(self) -> None:
        linked_web_users = self._web_user_repository.find({
            'linked_line_user_id': self._line_request_service.req_line_user_id,
            'is_linked_line': True,
        })
        linked_web_user_id = linked_web_users[0]._id if len(linked_web_users) != 0 else ''
        stocks = self._stock_repository.find({
            'owner_id__in': [
                linked_web_user_id,
                self._line_request_service.req_line_user_id,
            ],
            'status': 1,
        })

        if not stocks:
            self._line_response_service.add_message('登録中のアイテムはありません。')
            return

        with_expiry = sorted(
            [s for s in stocks if s.expiry_date is not None],
            key=lambda s: s.expiry_date,
        )
        without_expiry = [s for s in stocks if s.expiry_date is None]

        lines = [f'📋 登録中のアイテム（{len(stocks)}件）']

        if with_expiry:
            lines.append('')
            lines.append('⏰ 期限あり')
            for s in with_expiry:
                icon = _urgency_icon(s.expiry_date)
                lines.append(f'{icon} {s.item_name}  {_expiry_label(s.expiry_date)}')

        if without_expiry:
            lines.append('')
            lines.append('📌 期限なし')
            for s in without_expiry:
                elapsed = (datetime.now() - s.created_at).days + 1
                lines.append(f'• {s.item_name}（登録{elapsed}日目）')

        self._line_response_service.add_message('\n'.join(lines))
