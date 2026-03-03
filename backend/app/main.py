from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.database import engine, Base, SessionLocal
from app.core.auth import get_password_hash
from app.models.models import User, UserRole
from app.api.endpoints import auth, employees, config, payroll, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)

    # Create default admin user if none exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            admin = User(
                email="admin@mangoeyes.com",
                name="Admin",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            db.commit()
            print("Default admin user created: admin@mangoeyes.com / admin123")
    finally:
        db.close()

    yield


app = FastAPI(
    title="Employee Tracking & Payroll System",
    description="Automated payroll calculation with Insightful API integration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(config.router)
app.include_router(payroll.router)
app.include_router(audit.router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
