
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from app.database import get_db
from app.models.strategy import Strategy, StrategyRule, StrategyDeposit
from app.models.trade import Trade
from app.schemas.strategy import StrategyCreate, StrategyOut, StrategyRuleCreate, StrategyRuleOut, StrategyDepositCreate, StrategyDepositOut
from app.api.deps import get_current_user
from app.models.user import User
from app.models.trade import Trade
from app.services import trade_service
from app.schemas.trade import TradeCreate

router = APIRouter(prefix="/strategies", tags=["Strategies"])


# --- FIX FOR BUG 29: Pydantic Validation Models for Rule Params ---

class RiskRuleParams(BaseModel):
    requires_sl: Optional[bool] = None
    max_lot_size: Optional[float] = Field(
        None,
        gt=0,
        description="Must be greater than 0"
    )
    min_rr: Optional[float] = Field(
        None,
        gt=0,
        description="Must be strictly positive"
    )


class FilterRuleParams(BaseModel):
    # Example for future expansion, ensuring lists are actually lists
    sessions: Optional[List[str]] = None
    max_daily_trades: Optional[int] = Field(None, ge=1)


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


# --- ADDED: Update Strategy ---

@router.put("/{strategy_id}", response_model=StrategyOut)
def update_strategy(
    strategy_id: int,
    strategy_in: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    for key, value in strategy_in.model_dump().items():
        setattr(strategy, key, value)

    db.commit()
    db.refresh(strategy)
    return strategy


# --- ADDED: Delete Strategy ---

@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # FIX FOR BUG 24: Prevent cascading delete if trades exist
    trade_count = db.query(Trade).filter(Trade.strategy_id == strategy_id).count()

    if trade_count > 0:
        # Soft-delete the strategy by deactivating it
        strategy.is_active = False
        db.commit()
        # Note: We return 204 No Content here, which is standard for DELETE operations
        # even if it was a soft delete under the hood.
        # Alternatively, you could raise a 400 error to force the user to manually archive it.
        return None
    else:
        # Hard delete is safe because no historical trade data relies on it
        db.delete(strategy)
        db.commit()
        return None


# --- Strategy Rule Endpoints ---

# --- Helper: Sanitize JSON Parameters ---

def sanitize_rule_params(rule_type: str, params: dict) -> dict:
    if not params:
        return {}

    try:
        if rule_type == 'risk':
            validated = RiskRuleParams(**params)
            return validated.model_dump(exclude_none=True)

        elif rule_type == 'filter':
            validated = FilterRuleParams(**params)
            return validated.model_dump(exclude_none=True)

    except ValidationError as e:
        errors = [
            f"{err['loc'][0]}: {err['msg']}"
            for err in e.errors()
        ]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rule parameters: {', '.join(errors)}"
        )

    # For unhandled rule types, prevent arbitrary garbage data injection.
    return {}


@router.get("/{strategy_id}/rules", response_model=List[StrategyRuleOut])
def get_strategy_rules(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return db.query(StrategyRule).filter(StrategyRule.strategy_id == strategy_id).order_by(StrategyRule.sort_order).all()


# backend/app/api/strategies.py

@router.post("/{strategy_id}/rules", response_model=StrategyRuleOut)
def create_strategy_rule(
    strategy_id: int,
    rule_in: StrategyRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    clean_params = sanitize_rule_params(rule_in.rule_type, rule_in.params)

    new_rule = StrategyRule(
        **rule_in.model_dump(exclude={"params"}),
        params=clean_params,
        strategy_id=strategy_id
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return new_rule  # <-- ADD THIS LINE


# --- ADDED: Update Rule ---

@router.put("/{strategy_id}/rules/{rule_id}", response_model=StrategyRuleOut)
def update_strategy_rule(
    strategy_id: int,
    rule_id: int,
    rule_in: StrategyRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    rule = db.query(StrategyRule).filter(
        StrategyRule.id == rule_id,
        StrategyRule.strategy_id == strategy_id
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    clean_params = sanitize_rule_params(rule_in.rule_type, rule_in.params)

    update_data = rule_in.model_dump(exclude={"params"})

    for key, value in update_data.items():
        setattr(rule, key, value)

    rule.params = clean_params

    # Flush the rule update so the evaluator sees the new parameters
    db.flush()

    # FIX FOR BUG 28: Re-evaluate all OPEN trades for this strategy
    open_trades = db.query(Trade).filter(
        Trade.strategy_id == strategy_id,
        Trade.status == 'open'
    ).all()

    for trade in open_trades:
        checks_data = [
            {"rule_id": c.rule_id, "passed": c.passed}
            for c in trade.condition_checks
        ]

        current_state = TradeCreate(
            strategy_id=trade.strategy_id,
            instrument_id=trade.instrument_id,
            direction=trade.direction,
            entry_price=float(trade.entry_price),
            size=float(trade.size),
            stop_loss=float(trade.stop_loss) if trade.stop_loss else None,
            take_profit=float(trade.take_profit) if trade.take_profit else None,
            condition_checks=checks_data
        )

        new_violations = trade_service._evaluate_rule_violations(
            db,
            strategy_id,
            current_state
        )

        if trade.rule_violations != new_violations:
            trade.rule_violations = new_violations

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{strategy_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_rule(
    strategy_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    rule = db.query(StrategyRule).filter(StrategyRule.id == rule_id, StrategyRule.strategy_id == strategy_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(rule)
    db.commit()
    return None


# --- Strategy Deposit Endpoints ---

@router.get("/{strategy_id}/deposits", response_model=List[StrategyDepositOut])
def get_strategy_deposits(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return db.query(StrategyDeposit).filter(StrategyDeposit.strategy_id == strategy_id).order_by(StrategyDeposit.date.desc()).all()


@router.post("/{strategy_id}/deposits", response_model=StrategyDepositOut)
def create_strategy_deposit(
    strategy_id: int,
    deposit_in: StrategyDepositCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    deposit = db.query(StrategyDeposit).filter(StrategyDeposit.id == deposit_id, StrategyDeposit.strategy_id == strategy_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")

    db.delete(deposit)
    db.commit()
    return None


# --- ADDED: Strategy Balance Endpoint ---
@router.get("/{strategy_id}/balance")
def get_strategy_balance(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    deposits = db.query(StrategyDeposit).filter(StrategyDeposit.strategy_id == strategy_id).all()
    net_funding = sum([float(d.amount) if d.kind == 'deposit' else -float(d.amount) for d in deposits])

    # FIX FOR BUG 34: Removed Trade.status == 'closed'
    # to include P&L booked from open partial exits.
    realized_pnl = db.query(func.sum(Trade.pnl_realized)).filter(
        Trade.strategy_id == strategy_id
    ).scalar() or 0.0

    return {
        "net_funding": net_funding,
        "realized_pnl": float(realized_pnl),
        "total_balance": net_funding + float(realized_pnl)
    }
