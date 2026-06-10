"""Order id generation for finalize stage."""

from __future__ import annotations

import uuid


class OrderService:
    @staticmethod
    def generate_order_id() -> str:
        return f"ORDER-{uuid.uuid4().hex[:8].upper()}"
