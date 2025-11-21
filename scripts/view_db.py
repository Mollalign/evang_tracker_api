#!/usr/bin/env python3
"""
Script to view database contents after Alembic migrations.
Shows all tables and their data.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings
from datetime import datetime


def format_value(value, max_len=30):
    """Format values for display."""
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, (dict, list)):
        return str(value)[:max_len]
    val_str = str(value)
    return val_str[:max_len] + "..." if len(val_str) > max_len else val_str


async def view_database():
    """View all tables and their contents."""
    print("=" * 100)
    print("DATABASE CONTENTS VIEWER")
    print("=" * 100)
    db_url_display = settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "Hidden"
    print(f"Database: {db_url_display}")
    print()

    async with engine.connect() as conn:
        # Get all table names from information_schema
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        table_names = [row[0] for row in result.fetchall()]
        
        print(f"Found {len(table_names)} table(s): {', '.join(table_names)}")
        print()

        for table_name in table_names:
            print("=" * 100)
            print(f"TABLE: {table_name}")
            print("=" * 100)

            try:
                # Get column information
                col_result = await conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """))
                columns = col_result.fetchall()
                
                col_names = [col[0] for col in columns]
                print(f"Columns ({len(col_names)}):")
                for col_name, data_type, is_nullable in columns:
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    print(f"  - {col_name:30} {data_type:20} {nullable}")
                print()

                # Get row count
                count_result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                count = count_result.scalar()
                print(f"Total rows: {count}")
                print()

                if count > 0:
                    # Get all rows
                    result = await conn.execute(text(f"SELECT * FROM {table_name} ORDER BY 1 LIMIT 100"))
                    rows = result.fetchall()
                    
                    # Print header
                    header = " | ".join(f"{col:30}" for col in col_names)
                    print(header)
                    print("-" * len(header))
                    
                    # Print rows
                    for row in rows:
                        row_str = " | ".join(f"{format_value(val):30}" for val in row)
                        print(row_str)
                    
                    if count > 100:
                        print(f"\n... and {count - 100} more rows (showing first 100)")
                else:
                    print("(No data)")
                
                print()
                print()

            except Exception as e:
                print(f"Error reading table {table_name}: {e}")
                print()

        # Show Alembic version info
        print("=" * 100)
        print("ALEMBIC MIGRATION STATUS")
        print("=" * 100)
        try:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            if version:
                print(f"Current migration version: {version}")
                
                # Try to find the migration file
                migration_files = list(Path(__file__).parent.parent.glob(f"alembic/versions/*{version[:12]}*.py"))
                if migration_files:
                    print(f"Migration file: {migration_files[0].name}")
            else:
                print("No migration version found")
        except Exception as e:
            print(f"Could not read Alembic version: {e}")
        
        print()


if __name__ == "__main__":
    asyncio.run(view_database())

