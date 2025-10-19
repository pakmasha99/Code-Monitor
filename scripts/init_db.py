#!/usr/bin/env python
"""
Database initialization script
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import init_db, engine
from app.models import Base


def main():
    print("=' Initializing Code-Monitor database...")
    try:
        init_db()
        print(" Complete!")
        for table in Base.metadata.sorted_tables:
            print(f"   - {table.name}")
    except Exception as e:
        print(f"L Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
