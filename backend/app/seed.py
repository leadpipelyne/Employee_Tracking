import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import engine, Base, SessionLocal
from app.core.auth import get_password_hash
from app.models.models import User, UserRole


def seed_admin(email, password, name="Admin"):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print("[seed] Admin already exists: " + email)
            return
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        print("[seed] Created admin user: " + email)
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_admin("admin@example.com", "admin123", "Admin")
    seed_admin("admin@mangoeyes.com", "admin123", "Admin")
    print("[seed] Done.")
