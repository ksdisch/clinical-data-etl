"""Database connection utilities."""

from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Load .env from project root
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def get_engine() -> Engine:
    """Create a SQLAlchemy engine from DATABASE_URL environment variable."""
    import os

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://etl_user:etl_pass@localhost:5432/clinical_etl",
    )
    return create_engine(url)


def test_connection() -> bool:
    """Test the database connection. Returns True if successful."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
