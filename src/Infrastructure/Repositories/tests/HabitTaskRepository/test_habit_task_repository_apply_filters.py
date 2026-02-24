from src.Infrastructure.Repositories.HabitTaskRepository import HabitTaskRepository


class DummyDocRef:
    def __init__(self, doc_id: str):
        self.id = doc_id


class DummyCollection:
    def document(self, doc_id: str):
        return DummyDocRef(doc_id)


class DummyQuery:
    def __init__(self):
        self.calls = []

    def where(self, field, op, value):
        self.calls.append((field, op, value))
        return self


def test_apply_filters_converts_id_eq_to_document_reference():
    repository = HabitTaskRepository()
    repository._collection = lambda: DummyCollection()
    query = DummyQuery()

    repository._apply_filters(query, {"_id": "task-1"})

    assert len(query.calls) == 1
    _, op, value = query.calls[0]
    assert op == "=="
    assert isinstance(value, DummyDocRef)
    assert value.id == "task-1"


def test_apply_filters_converts_id_in_to_document_references():
    repository = HabitTaskRepository()
    repository._collection = lambda: DummyCollection()
    query = DummyQuery()

    repository._apply_filters(query, {"_id__in": ["task-1", "task-2"]})

    assert len(query.calls) == 1
    _, op, value = query.calls[0]
    assert op == "in"
    assert len(value) == 2
    assert all(isinstance(v, DummyDocRef) for v in value)
    assert [v.id for v in value] == ["task-1", "task-2"]
