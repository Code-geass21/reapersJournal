from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.instrument import Instrument, Market
from app.schemas.instrument import InstrumentOut, InstrumentCreate
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

@router.post("/", response_model=InstrumentOut)
def create_instrument(
    instrument_in: InstrumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify the market exists
    market = db.query(Market).filter(Market.code == instrument_in.market_code).first()
    if not market:
        raise HTTPException(status_code=400, detail="Invalid market code")

    # Check for duplicates
    existing = db.query(Instrument).filter(Instrument.symbol == instrument_in.symbol).first()
    if existing:
        raise HTTPException(status_code=400, detail="Instrument symbol already exists")

    new_instrument = Instrument(**instrument_in.model_dump())
    db.add(new_instrument)
    db.commit()
    db.refresh(new_instrument)
    return new_instrument
