from typing import List

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.log import LogCreate, LogResponse
from app.services.log_service import create_log, get_log, list_logs


router = APIRouter()


@router.post("/", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def create_log_endpoint(payload: LogCreate, session: Session = Depends(get_session)):
    return create_log(session, payload)


@router.get("/{log_id}", response_model=LogResponse)
def get_log_endpoint(log_id: int, session: Session = Depends(get_session)):
    log = get_log(session, log_id)
    return log


@router.get("/", response_model=List[LogResponse])
def list_logs_endpoint(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    return list_logs(session, skip=skip, limit=limit)


