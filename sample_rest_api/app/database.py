import os
import databases
import sqlalchemy
from sqlalchemy import create_engine, MetaData
from datetime import datetime

# Default to file-based SQLite
DATABASE_URL = "sqlite:///./test.db"

# Use in-memory SQLite if MEMORY_DB is set to true
if os.environ.get("MEMORY_DB", "").lower() in ("true", "1", "t", "yes"):
    print("Using in-memory SQLite database")
    # Special URI for shared in-memory database that persists throughout the application
    DATABASE_URL = "sqlite:///file:memdb?mode=memory&cache=shared&uri=true"
else:
    print(f"Using file-based SQLite database: {DATABASE_URL}")

# SQLAlchemy database instance
database = databases.Database(DATABASE_URL)

# SQLAlchemy metadata object
metadata = sqlalchemy.MetaData()

# Define tables
categories = sqlalchemy.Table(
    "categories",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, default=datetime.now),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, default=datetime.now, onupdate=datetime.now),
)

products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("category_id", sqlalchemy.String, sqlalchemy.ForeignKey("categories.id"), nullable=False),
    sqlalchemy.Column("in_stock", sqlalchemy.Boolean, default=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, default=datetime.now),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, default=datetime.now, onupdate=datetime.now),
)

# Create database engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Function to create tables
def create_tables():
    metadata.create_all(engine) 