from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.auth import get_current_user, get_password_hash
from app.models.models import User, UserRole, AuditLog
from app.schemas.schemas import UserCreate, UserResponse, UserRole as SchemaUserRole

router = APIRouter(prefix="/api/users", tags=["User Management"])


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users. Admin only."""
    return db.query(User).order_by(User.name).all()


@router.post("", response_model=UserResponse)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user. Admin only."""
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
    )
    db.add(user)
    db.flush()

    db.add(AuditLog(
        action="create_user",
        entity_type="user",
        entity_id=user.id,
        new_value=json.dumps({"email": data.email, "name": data.name, "role": data.role.value}),
        performed_by=current_user.email,
    ))
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    role: str = None,
    name: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a user's role or status. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id and is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    old_values = {}
    if role is not None:
        old_values["role"] = user.role.value
        user.role = role
    if name is not None:
        old_values["name"] = user.name
        user.name = name
    if is_active is not None:
        old_values["is_active"] = user.is_active
        user.is_active = is_active

    if old_values:
        new_values = {}
        if role is not None:
            new_values["role"] = role
        if name is not None:
            new_values["name"] = name
        if is_active is not None:
            new_values["is_active"] = is_active

        db.add(AuditLog(
            action="update_user",
            entity_type="user",
            entity_id=user.id,
            old_value=json.dumps(old_values),
            new_value=json.dumps(new_values),
            performed_by=current_user.email,
        ))
        db.commit()
        db.refresh(user)

    return user


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Reset a user's password. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(new_password)

    db.add(AuditLog(
        action="reset_password",
        entity_type="user",
        entity_id=user.id,
        performed_by=current_user.email,
    ))
    db.commit()
    return {"message": f"Password reset for {user.email}"}
