#!/bin/bash

set -e  # 에러 발생 시 즉시 종료

# 간단한 로깅 함수
log() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

# 1. 필수 패키지 설치
log "패키지 업데이트 중..."
apt-get update || {
    log_error "패키지 업데이트 실패"
    exit 1
}

log "필수 패키지 설치 중..."
apt-get install -y curl sudo wget unzip tmux || {
    log_error "패키지 설치 실패"
    exit 1
}
sudo apt install -y openjdk-17-jdk || {
    log_error "Java 설치 실패"
    exit 1
}

# 3. Grobid 다운로드 및 설치
log "Grobid 다운로드 중..."
wget https://github.com/kermitt2/grobid/archive/0.8.2.zip || {
    log_error "Grobid 다운로드 실패"
    exit 1
}

log "압축 해제 중..."
unzip 0.8.2.zip || {
    log_error "압축 해제 실패"
    exit 1
}

log "Grobid 빌드 중..."
cd grobid-0.8.2 || {
    log_error "grobid-0.8.2 디렉토리로 이동 실패"
    exit 1
}

./gradlew clean install || {
    log_error "Grobid 빌드 실패"
    exit 1
}


log "임시 파일 정리 중..."
rm -rf 0.8.2.zip

log "설치 완료!"

log "Grobid 서버 실행중..."
GROBID_DIR="$(pwd)"  # 현재 디렉토리 (grobid-0.8.2)

# tmux 세션이 이미 존재하는지 확인
if tmux has-session -t grobid 2>/dev/null; then
    log "기존 grobid tmux 세션을 종료하고 재시작합니다..."
    tmux kill-session -t grobid || true
fi

# 새 tmux 세션 생성 및 서버 실행
tmux new-session -d -s grobid -c "$GROBID_DIR" "./gradlew run" || {
    log_error "Grobid 서버 실행 실패"
    exit 1
}

log "Grobid 서버가 tmux 세션(grobid)에서 실행 중입니다."
log "서버 확인: http://localhost:8070"
log "tmux 세션 확인: tmux attach -t grobid"