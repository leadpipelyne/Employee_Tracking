"""
Seed script: creates default admin users if they don't already exist.
Run with: python -m app.seed  (from the /app working directory)
"""

import sys
import os

# Ensure the app package is importable when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base, SessionLocal
from app.core.auth import get_password_hash
from app.models.models import User, UserRole


def seed_admin(email, password, name="Admin"):
          """Create an admin user with the given email if one does not already exist."""
          db = SessionLocal()
          try:
                        existing = db.query(User).filter(User.email == email).first()
                        if existing:
                                          print("[seed] Admin already exists: " + email + " - skipping.")
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
          # Ensure all tables exist before seeding
          Base.metadata.create_all(bind=engine)

    # Default admin required by task spec
          seed_admin("admin@example.com", "admin123", "Admin")

    # Keep the original mangoeyes admin as well
          seed_admin("admin@mangoeyes.com", "admin123", "Admin")

    print("[seed] Done.")
