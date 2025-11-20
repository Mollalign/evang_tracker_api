# scripts/add_admin.py
import asyncio
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

async def create_initial_admin():
    async with AsyncSessionLocal() as db:
        admin_email = "molledan69@gmail.com"

        # Check if admin already exists
        result = await db.execute(select(User).filter(User.email == admin_email))
        existing_admin = result.scalars().first()

        if existing_admin:
            print("⚠️ Admin already exists.")
            return

        # Create admin user
        admin_user = User(
            full_name="Super Admin",
            email=admin_email,
            password_hash=get_password_hash("SuperAdmin@123"),  # Replace with a secure password
            role=UserRole.admin
        )
        db.add(admin_user)
        await db.commit()
        print("✅ Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(create_initial_admin())
