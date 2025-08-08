from typing import List, Optional

from sqlmodel import Session, select

from app.models.log import Log
from app.schemas.log import LogCreate


def create_log(session: Session, data: LogCreate) -> Log:
    log = Log.model_validate(data)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def get_log(session: Session, log_id: int) -> Optional[Log]:
    return session.get(Log, log_id)


def list_logs(session: Session, skip: int = 0, limit: int = 10) -> List[Log]:
    query = select(Log).offset(skip).limit(limit)
    return session.exec(query).all()


