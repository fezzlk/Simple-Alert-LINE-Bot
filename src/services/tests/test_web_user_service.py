from typing import Dict, List

from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.services.WebUserService import WebUserService


class InMemoryWebUserRepository(IWebUserRepository):
    def __init__(self, initial: List[WebUser] = None):
        self._items = list(initial or [])
        self.created_count = 0

    def create(self, new_web_user: WebUser) -> WebUser:
        self._items.append(new_web_user)
        self.created_count += 1
        return new_web_user

    def update(self, query: Dict[str, any], new_web_user: WebUser) -> int:
        return 0

    def delete(self, query: Dict[str, any]) -> int:
        return 0

    def find(self, query: Dict[str, any]) -> List[WebUser]:
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
    repo = InMemoryWebUserRepository()
    service = WebUserService(web_user_repository=repo)
    user = WebUser(
        _id='U0123456789abcdefghijklmnopqrstu1',
        web_user_name='dummy_web_user',
        web_user_email='dummy@example.com',
    )

    result = service.find_or_create(new_web_user=user)

    assert result == user
    assert repo.created_count == 1
    assert repo.find({'web_user_email': user.web_user_email}) == [user]


def test_find_or_create_returns_existing_without_create():
    existing = WebUser(
        _id='U0123456789abcdefghijklmnopqrstu1',
        web_user_name='dummy_web_user',
        web_user_email='dummy@example.com',
    )
    repo = InMemoryWebUserRepository(initial=[existing])
    service = WebUserService(web_user_repository=repo)
    another = WebUser(
        _id='U0123456789abcdefghijklmnopqrstu2',
        web_user_name='another_name',
        web_user_email='dummy@example.com',
    )

    result = service.find_or_create(new_web_user=another)

    assert result == another
    assert repo.created_count == 0
    assert repo.find({'web_user_email': existing.web_user_email}) == [existing]
