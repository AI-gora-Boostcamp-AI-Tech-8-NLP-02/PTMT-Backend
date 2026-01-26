#!/bin/bash
# ===========================================
# PTMT Backend Test Script
# 테스트 실행 및 커버리지 리포트 생성
# ===========================================

set -e

echo "🧪 Running tests..."

# pytest 실행 with coverage
pytest tests/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:coverage_html \
    -v

echo "✅ Tests completed!"
echo "📊 Coverage report available at: coverage_html/index.html"
