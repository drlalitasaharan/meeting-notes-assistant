# app/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from packages.shared.env import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)

