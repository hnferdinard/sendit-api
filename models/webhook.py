from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
class Webhook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    event_type: str
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    retry_count: int = Field(default=0)
    last_triggered: Optional[datetime] = None
class WebhookCreate(SQLModel):
    url: str
    event_type: str
