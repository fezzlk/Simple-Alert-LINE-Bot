from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import firestore
from google.cloud.firestore_v1.field_path import FieldPath

from src.Domains.Entities.HabitTask import HabitTask
from src.firestore_client import firestore_client
from src.firestore_query import build_filters


class HabitTaskRepository:
    _collection_name = "habit_tasks"

    def _collection(self):
        return firestore_client.collection(self._collection_name)

    def _apply_filters(self, query_ref, query: Dict[str, Any]):
        filters = build_filters(query)
        for field, op, value in filters:
            if field in ("_id", "id"):
                field_ref = FieldPath.document_id()
                if op == "in":
                    if value == []:
                        return query_ref.where(field_ref, "==", "__no_results__")
                    if isinstance(value, list):
                        value = [
                            self._collection().document(v) if isinstance(v, str) else v
                            for v in value
                            if v not in (None, "")
                        ]
                        if value == []:
                            return query_ref.where(field_ref, "==", "__no_results__")
                elif op == "==":
                    if value in (None, ""):
                        return query_ref.where("___no_results__", "==", True)
                    if isinstance(value, str):
                        value = self._collection().document(value)
            else:
                field_ref = field
            if op == "in" and value == []:
                return query_ref.where(field_ref, "==", "__no_results__")
            query_ref = query_ref.where(field_ref, op, value)
        return query_ref

    def create(self, new_habit_task: HabitTask) -> HabitTask:
        data = new_habit_task.__dict__.copy()
        if data["_id"] is None:
            data.pop("_id")
            doc_ref = self._collection().document()
        else:
            doc_ref = self._collection().document(str(data["_id"]))
        doc_ref.set(data)
        new_habit_task._id = doc_ref.id
        return new_habit_task

    def update(self, query: Dict[str, Any], new_values: Dict[str, Any]) -> int:
        new_values["updated_at"] = datetime.now()
        query_ref = self._apply_filters(self._collection(), query)
        docs = list(query_ref.stream())
        for doc in docs:
            doc.reference.update(new_values)
        return len(docs)

    def find(
        self,
        query: Dict[str, Any] = {},
        sort: Optional[List[Tuple[str, Any]]] = None,
    ) -> List[HabitTask]:
        query_ref = self._apply_filters(self._collection(), query)
        records = query_ref.stream()
        items = []
        for record in records:
            data = record.to_dict() or {}
            data["_id"] = record.id
            items.append(HabitTask(**data))

        items.sort(key=lambda h: (h.notify_time or "", h.task_name or "", h._id or ""))
        if sort is None:
            return items
        for field, direction in reversed(sort):
            reverse = direction in ("desc", "descending", firestore.Query.DESCENDING)
            if field in ("_id", "id"):
                items.sort(key=lambda i: i._id or "", reverse=reverse)
            else:
                items.sort(key=lambda i: getattr(i, field, None) or "", reverse=reverse)
        return items

    def delete(self, query: Dict[str, Any] = {}) -> int:
        query_ref = self._apply_filters(self._collection(), query)
        docs = list(query_ref.stream())
        for doc in docs:
            doc.reference.delete()
        return len(docs)
