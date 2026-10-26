from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyOut
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/strategies", tags=["Strategies"])

@router.get("/", response_model=List[StrategyOut])
def get_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only return strategies belonging to the logged-in user
    return db.query(Strategy).filter(Strategy.user_id == current_user.id).all()

@router.post("/", response_model=StrategyOut)
def create_strategy(
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Convert Pydantic model to dict and append the secure user_id
    new_strategy = Strategy(**strategy_in.model_dump(), user_id=current_user.id)
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    return new_strategy
