# #!/bin/bash
# # ===========================================
# # PTMT Backend Prestart Script
# # DB 대기 및 마이그레이션 수행
# # ===========================================

# set -e

# echo "🚀 Starting prestart script..."

# # PostgreSQL 연결 대기
# echo "⏳ Waiting for PostgreSQL..."
# while ! nc -z ${DB_HOST:-localhost} ${DB_PORT:-5432}; do
#     sleep 1
# done
# echo "✅ PostgreSQL is ready!"

# # Alembic 마이그레이션 실행
# echo "🔄 Running database migrations..."
# alembic upgrade head
# echo "✅ Migrations completed!"

# echo "🎉 Prestart script finished!"
