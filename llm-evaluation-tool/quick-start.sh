#!/bin/bash
# Quick Start Script for LLM Evaluation Tool

echo "================================"
echo "LLM 평가 도구 - 빠른 시작"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    echo "   Docker를 먼저 설치해주세요: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker 확인 완료"
echo ""

# Create necessary directories
echo "📁 디렉토리 생성 중..."
mkdir -p data database
echo "✓ 디렉토리 생성 완료"
echo ""

# Build Docker image
echo "🔨 Docker 이미지 빌드 중..."
docker build -t llm-eval-tool .
if [ $? -ne 0 ]; then
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi
echo "✓ Docker 이미지 빌드 완료"
echo ""

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=llm-eval)" ]; then
    echo "🛑 기존 컨테이너 중지 및 제거 중..."
    docker stop llm-eval 2>/dev/null
    docker rm llm-eval 2>/dev/null
    echo "✓ 기존 컨테이너 제거 완료"
    echo ""
fi

# Run container
echo "🚀 컨테이너 실행 중..."
docker run -d \
    -p 8080:8080 \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/database:/app/database" \
    --name llm-eval \
    llm-eval-tool

if [ $? -ne 0 ]; then
    echo "❌ 컨테이너 실행 실패"
    exit 1
fi
echo "✓ 컨테이너 실행 완료"
echo ""

# Wait for container to be ready
echo "⏳ 서버 시작 대기 중..."
sleep 3

# Initialize admin user
echo "👤 관리자 계정 생성 중..."
echo ""
echo "기본값을 사용하려면 Enter를 누르세요:"
echo "  - 관리자: admin / admin123"
echo "  - 평가자: evaluator / eval123"
echo ""

docker exec -it llm-eval python init_admin.py

echo ""
echo "================================"
echo "✅ 설치 완료!"
echo "================================"
echo ""
echo "🌐 웹 브라우저에서 다음 주소로 접속하세요:"
echo "   http://localhost:8080"
echo ""
echo "📊 유용한 명령어:"
echo "   로그 확인: docker logs llm-eval"
echo "   컨테이너 중지: docker stop llm-eval"
echo "   컨테이너 시작: docker start llm-eval"
echo "   컨테이너 재시작: docker restart llm-eval"
echo ""
