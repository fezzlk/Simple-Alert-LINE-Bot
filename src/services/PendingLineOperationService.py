from datetime import datetime
from typing import Any, Dict, Optional

from src.firestore_client import firestore_client


class PendingLineOperationService:
    _collection_name = "line_pending_operations"

    def _collection(self):
        return firestore_client.collection(self._collection_name)

    def save(self, line_user_id: str, operation: Dict[str, Any]) -> None:
        payload = {
            "line_user_id": line_user_id,
            "operation": operation,
            "updated_at": datetime.now(),
        }
        self._collection().document(line_user_id).set(payload)

    def get(self, line_user_id: str) -> Optional[Dict[str, Any]]:
        doc = self._collection().document(line_user_id).get()
        if not doc.exists:
            return None
        return doc.to_dict()

    def clear(self, line_user_id: str) -> None:
        self._collection().document(line_user_id).delete()
