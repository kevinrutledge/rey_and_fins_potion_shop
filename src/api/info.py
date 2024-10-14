import logging
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

logger = logging.getLogger(__name__)

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """
    Share current time.
    """
    logger.debug(f"Current time: {timestamp}")

    return "OK"
