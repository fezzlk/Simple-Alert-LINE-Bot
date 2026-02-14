from datetime import datetime
import re

from flask import Request, request
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from werkzeug.exceptions import BadRequest
from src.models.PageContents import PageContents


class UpdateStockUseCase(IUseCase):
    def __init__(self, stock_repository: IStockRepository):
        self._stock_repository = stock_repository

    def execute(self, page_contents: PageContents) -> None:
        request: Request = page_contents.request
        form = request.form
        owner_web: WebUser = page_contents.login_user
        owner_line_id = owner_web.linked_line_user_id if owner_web.is_linked_line_user else ''

        stock_id = form.get('stock_id', None)
        if stock_id is None or stock_id == '':
            raise BadRequest('stock_id が指定されていません。')
        new_values = {}

        def _parse_date_value(raw: str) -> datetime:
            cleaned = raw.strip()
            # Drop trailing timezone abbreviations like "JST"
            cleaned = re.sub(r'\s+[A-Za-z]{2,5}$', '', cleaned)
            cleaned = cleaned.replace('/', '-').replace('T', ' ')
            for fmt in (
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d %H:%M:%S',
            ):
                try:
                    return datetime.strptime(cleaned, fmt)
                except ValueError:
                    continue
            raise BadRequest("日付として不適切です。")

        for key in form:
            val = form.get(key)

            if key == 'item_name':
                if val == '':
                    raise BadRequest("名前は必須です。")
                new_values[key] = val

            elif key == 'str_expiry_date':
                if val != '':
                    new_values['expiry_date'] = _parse_date_value(val)
                else:
                    new_values['expiry_date'] = None

            elif key == 'str_created_at':
                if val == '':
                    raise BadRequest("日付は必須です。")
                new_values['created_at'] = _parse_date_value(val)
            elif key == 'notify_status':
                if val is None:
                    continue
                upper = val.strip().upper()
                if upper not in ('ON', 'OFF'):
                    raise BadRequest('通知は ON または OFF を指定してください。')
                new_values['notify_enabled'] = upper == 'ON'

        res = self._stock_repository.update(
            query={
                '_id': stock_id,
                'owner_id__in': [owner_web._id, owner_line_id],
            },
            new_values=new_values,
        )
