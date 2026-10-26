from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.instrument import Instrument
from app.schemas.instrument import InstrumentOut
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/instruments", tags=["Instruments"])

@router.get("/", response_model=List[InstrumentOut])
def get_instruments(
    market: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Instrument).filter(Instrument.is_active == True)
    if market:
        query = query.filter(Instrument.market_code == market)
    return query.all()
