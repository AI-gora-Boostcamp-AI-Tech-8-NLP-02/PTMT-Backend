#!/bin/bash

# FastAPI 서버 실행 스크립트

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
