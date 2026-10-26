from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
# Ensure StrategyDeposit is imported here:
from app.models.strategy import Strategy, StrategyRule, StrategyDeposit
# Ensure StrategyDepositCreate and StrategyDepositOut are imported here:
from app.schemas.strategy import StrategyCreate, StrategyOut, StrategyRuleCreate, StrategyRuleOut, StrategyDepositCreate, StrategyDepositOut
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/strategies", tags=["Strategies"])

# --- Strategy Endpoints ---

@router.get("/", response_model=List[StrategyOut])
def get_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Strategy).filter(Strategy.user_id == current_user.id).all()

@router.post("/", response_model=StrategyOut)
def create_strategy(
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_strategy = Strategy(**strategy_in.model_dump(), user_id=current_user.id)
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    return new_strategy

# --- Strategy Rule Endpoints ---

@router.get("/{strategy_id}/rules", response_model=List[StrategyRuleOut])
def get_strategy_rules(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return db.query(StrategyRule).filter(StrategyRule.strategy_id == strategy_id).order_by(StrategyRule.sort_order).all()

@router.post("/{strategy_id}/rules", response_model=StrategyRuleOut)
def create_strategy_rule(
    strategy_id: int,
    rule_in: StrategyRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    new_rule = StrategyRule(**rule_in.model_dump(), strategy_id=strategy_id)
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.delete("/{strategy_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_rule(
    strategy_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership of the parent strategy
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    rule = db.query(StrategyRule).filter(StrategyRule.id == rule_id, StrategyRule.strategy_id == strategy_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return None

@router.get("/{strategy_id}/deposits", response_model=List[StrategyDepositOut])
def get_strategy_deposits(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Return ordered by newest first
    return db.query(StrategyDeposit).filter(StrategyDeposit.strategy_id == strategy_id).order_by(StrategyDeposit.date.desc()).all()

@router.post("/{strategy_id}/deposits", response_model=StrategyDepositOut)
def create_strategy_deposit(
    strategy_id: int,
    deposit_in: StrategyDepositCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    new_deposit = StrategyDeposit(**deposit_in.model_dump(), strategy_id=strategy_id)
    db.add(new_deposit)
    db.commit()
    db.refresh(new_deposit)
    return new_deposit

@router.delete("/{strategy_id}/deposits/{deposit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_deposit(
    strategy_id: int,
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify ownership of the parent strategy
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    deposit = db.query(StrategyDeposit).filter(StrategyDeposit.id == deposit_id, StrategyDeposit.strategy_id == strategy_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")

    db.delete(deposit)
    db.commit()
    return None
