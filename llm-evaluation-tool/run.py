#!/usr/bin/env python3
"""
LLM Evaluation Tool - Main Application Entry Point
"""
import os
import sys
from app import create_app
from config import Config

def main():
    """Run the Flask application"""
    app = create_app()

    print("=" * 60)
    print("LLM 평가 도구 시작 중...")
    print("=" * 60)
    print(f"데이터베이스 경로: {app.config['DATABASE_PATH']}")
    print(f"데이터셋 경로: {app.config['DATASET_PATH']}")
    print(f"서버 주소: http://{app.config['HOST']}:{app.config['PORT']}")
    print("=" * 60)

    # Load dataset if specified and exists
    dataset_path = app.config['DATASET_PATH']
    if os.path.exists(dataset_path):
        try:
            import json
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            app.db.load_dataset(dataset)
            print(f"✓ 데이터셋 로드 완료: {len(dataset)}개 예제")
        except Exception as e:
            print(f"⚠ 데이터셋 로드 실패: {e}")
    else:
        print(f"⚠ 데이터셋 파일을 찾을 수 없습니다: {dataset_path}")

    print("=" * 60)
    print("\n서버가 시작되었습니다. 웹 브라우저에서 접속하세요.\n")

    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )

if __name__ == '__main__':
    main()
