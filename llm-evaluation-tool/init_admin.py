#!/usr/bin/env python3
"""
Initialize admin user for the LLM Evaluation Tool
"""
import os
import sys
from app.models import Database
from config import Config

def main():
    """Create initial admin and evaluator accounts"""

    # Ensure database directory exists
    db_dir = os.path.dirname(Config.DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    db = Database(Config.DATABASE_PATH)

    print("=" * 60)
    print("LLM 평가 도구 - 초기 사용자 설정")
    print("=" * 60)

    # Create admin
    admin_username = input("관리자 사용자명 (기본값: admin): ").strip() or "admin"
    admin_password = input("관리자 비밀번호 (기본값: admin123): ").strip() or "admin123"

    admin_id = db.create_user(admin_username, admin_password, role='admin')
    if admin_id:
        print(f"✓ 관리자 계정 생성 완료: {admin_username}")
    else:
        print(f"⚠ 관리자 계정이 이미 존재합니다: {admin_username}")

    # Create evaluator
    create_evaluator = input("\n평가자 계정을 생성하시겠습니까? (y/n, 기본값: y): ").strip().lower()
    if create_evaluator != 'n':
        eval_username = input("평가자 사용자명 (기본값: evaluator): ").strip() or "evaluator"
        eval_password = input("평가자 비밀번호 (기본값: eval123): ").strip() or "eval123"

        eval_id = db.create_user(eval_username, eval_password, role='evaluator')
        if eval_id:
            print(f"✓ 평가자 계정 생성 완료: {eval_username}")
        else:
            print(f"⚠ 평가자 계정이 이미 존재합니다: {eval_username}")

    print("=" * 60)
    print("초기 설정 완료!")
    print("=" * 60)

if __name__ == '__main__':
    main()
