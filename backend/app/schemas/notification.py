from datetime import datetime
from typing import Any

from app.models.notification import (
    NotificationType,
)
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int

    type: NotificationType

    title: str
    body: str

    data: dict[str, Any]

    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]

    unread_count: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationReadAllResponse(BaseModel):
    updated_count: int
