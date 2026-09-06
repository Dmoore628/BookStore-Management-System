from sqlalchemy import create_engine, text
from domain_services.database import Base
engine = create_engine("sqlite:///:memory:")
import domain_services.entities
Base.metadata.create_all(engine)
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    print(f"Tables: {result}")

