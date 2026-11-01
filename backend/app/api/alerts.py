from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertOut
from app.api.deps import get_current_user
from app.models.user import User
from app.services import trade_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/", response_model=List[AlertOut])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch active alerts (new or seen) for the user."""
    return db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.status.in_(['new', 'seen'])
    ).order_by(Alert.created_at.desc()).all()

@router.post("/{alert_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an alert as dismissed."""
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = 'dismissed'
    db.commit()
    return None

@router.post("/{alert_id}/confirm-close", status_code=status.HTTP_204_NO_CONTENT)
def confirm_alert_action(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Action an SL/TP alert by automatically closing the trade using
    the trigger price as the exit price.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if not alert.trade_id or alert.kind not in ['sl_hit', 'tp_hit']:
        raise HTTPException(status_code=400, detail="Alert cannot be actioned this way")

    # Extract the triggered price from the alert message.
    # Example format: "Stop Loss (1.105) hit for EURUSD at 1.104"
    try:
        current_price = float(alert.message.split(" at ")[-1])
    except ValueError:
        raise HTTPException(status_code=400, detail="Could not parse execution price from alert")

    # Update trade via service to ensure P&L math and audit logging occurs
    from app.schemas.trade import TradeUpdate
    update_data = TradeUpdate(status="closed", exit_price=current_price)
    trade_service.update_trade(db, current_user.id, alert.trade_id, update_data)

    alert.status = 'actioned'
    db.commit()
    return None
