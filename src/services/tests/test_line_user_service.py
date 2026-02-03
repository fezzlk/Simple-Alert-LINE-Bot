from typing import Dict, List

from src.Domains.Entities.LineUser import LineUser
from src.Domains.IRepositories.ILineUserRepository import ILineUserRepository
from src.services.LineUserService import LineUserService


class InMemoryLineUserRepository(ILineUserRepository):
    def __init__(self, initial: List[LineUser] = None):
        self._items = list(initial or [])
        self.created_count = 0

    def create(self, new_line_user: LineUser) -> LineUser:
        self._items.append(new_line_user)
        self.created_count += 1
        return new_line_user

    def update(self, query: Dict[str, any], new_line_user: LineUser) -> int:
        return 0

    def delete(self, query: Dict[str, any]) -> int:
        return 0

    def find(self, query: Dict[str, any]) -> List[LineUser]:
        if not query:
            return list(self._items)
        result = []
        for item in self._items:
            matched = True
            for key, value in query.items():
                if getattr(item, key) != value:
                    matched = False
                    break
            if matched:
                result.append(item)
        return result


def test_find_or_create_creates_when_missing():
    repo = InMemoryLineUserRepository()
    service = LineUserService(line_user_repository=repo)
    user = LineUser(
        line_user_name='dummy_line_user',
        line_user_id='U0123456789abcdefghijklmnopqrstu1',
    )

    result = service.find_or_create(new_line_user=user)

    assert result == user
    assert repo.created_count == 1
    assert repo.find({'line_user_id': user.line_user_id}) == [user]


def test_find_or_create_returns_existing_without_create():
    existing = LineUser(
        line_user_name='dummy_line_user',
        line_user_id='U0123456789abcdefghijklmnopqrstu1',
    )
    repo = InMemoryLineUserRepository(initial=[existing])
    service = LineUserService(line_user_repository=repo)
    another = LineUser(
        line_user_name='another_name',
        line_user_id='U0123456789abcdefghijklmnopqrstu1',
    )

    result = service.find_or_create(new_line_user=another)

    assert result == another
    assert repo.created_count == 0
    assert repo.find({'line_user_id': existing.line_user_id}) == [existing]
