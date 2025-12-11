#!/usr/bin/env python3
"""
Admin 계정 생성 스크립트

서버 실행 전에 Admin 계정을 생성하거나, 기존 사용자를 Admin으로 승격시킵니다.

사용법:
    # 새 Admin 계정 생성
    python scripts/create_admin.py --email admin@example.com --password yourpassword

    # 기존 사용자를 Admin으로 승격
    python scripts/create_admin.py --email user@example.com --promote
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import User, Profile
from app.auth.services.security import hash_password


async def create_admin(email: str, password: str) -> None:
    """새 Admin 계정 생성"""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"❌ Error: User with email '{email}' already exists.")
            print(f"   Use --promote flag to upgrade existing user to admin.")
            return

        # Create admin user
        hashed_pwd = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed_pwd,
            role="admin"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create empty profile
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()

        print(f"✅ Admin account created successfully!")
        print(f"   Email: {email}")
        print(f"   Role: admin")
        print(f"   User ID: {user.id}")


async def promote_to_admin(email: str) -> None:
    """기존 사용자를 Admin으로 승격"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ Error: User with email '{email}' not found.")
            return

        if user.role == "admin":
            print(f"ℹ️  User '{email}' is already an admin.")
            return

        # Promote to admin
        user.role = "admin"
        await db.commit()

        print(f"✅ User promoted to admin successfully!")
        print(f"   Email: {email}")
        print(f"   Role: admin → admin")
        print(f"   User ID: {user.id}")


async def list_admins() -> None:
    """모든 Admin 계정 목록 표시"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.role == "admin").order_by(User.created_at)
        )
        admins = result.scalars().all()

        if not admins:
            print("ℹ️  No admin accounts found.")
            return

        print(f"\n📋 Admin Accounts ({len(admins)} total):")
        print("-" * 80)
        for admin in admins:
            status = "🟢 Active" if admin.is_active and not admin.is_blocked else "🔴 Inactive"
            print(f"  • {admin.email}")
            print(f"    ID: {admin.id} | Status: {status} | Created: {admin.created_at.strftime('%Y-%m-%d')}")
        print("-" * 80)


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Admin 계정 생성 및 관리",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 새 Admin 계정 생성
  python scripts/create_admin.py --email admin@example.com --password yourpassword

  # 기존 사용자를 Admin으로 승격
  python scripts/create_admin.py --email user@example.com --promote

  # 모든 Admin 계정 목록 보기
  python scripts/create_admin.py --list
        """
    )

    parser.add_argument("--email", type=str, help="사용자 이메일")
    parser.add_argument("--password", type=str, help="비밀번호 (새 계정 생성 시)")
    parser.add_argument("--promote", action="store_true", help="기존 사용자를 Admin으로 승격")
    parser.add_argument("--list", action="store_true", help="모든 Admin 계정 목록 표시")

    args = parser.parse_args()

    # Initialize database
    await init_db()

    if args.list:
        await list_admins()
    elif args.promote:
        if not args.email:
            print("❌ Error: --email is required with --promote")
            parser.print_help()
            sys.exit(1)
        await promote_to_admin(args.email)
    elif args.email and args.password:
        await create_admin(args.email, args.password)
    else:
        print("❌ Error: Invalid arguments")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
