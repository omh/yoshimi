from datetime import datetime

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    DateTime,
)
from sqlalchemy.orm import (
    backref,
    relationship,
)

from yoshimi.content import Base


class TrashContent(Base):
    __tablename__ = 'trash'

    content_id = Column(
        Integer,
        ForeignKey('content.id', ondelete='CASCADE'),
        primary_key=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    content = relationship(
        'Content',
        foreign_keys=[content_id],
        backref=backref(
            'trash_info',
            uselist=False,
        ),
    )
