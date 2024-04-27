import sqlalchemy as sa
from sqlalchemy import func
from datetime import datetime

from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()


class TimeMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )
