import asyncio
import os
import sys

# Add project root to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prisma import Prisma
from app.core.security import get_password_hash

async def main() -> None:
    db = Prisma()
    await db.connect()
    
    # Check if admin exists
    admin = await db.user.find_unique(where={"username": "admin"})
    if admin:
        print("Admin user already exists.")
        await db.disconnect()
        return

    # Create Cabinet
    cabinet = await db.cabinet.create(
        data={
            "name": "Cabinet Postefinances Par Défaut"
        }
    )
    
    # Create Admin
    hashed_pwd = get_password_hash("admin123")
    user = await db.user.create(
        data={
            "username": "admin",
            "hashed_password": hashed_pwd,
            "role": "ADMIN",
            "cabinetId": cabinet.id
        }
    )
    print(f"Admin created successfully! Username: {user.username}, Password: admin123")
    
    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
