#!/bin/bash

# 1. 환경 변수 로드 (.env 파일에서 TUNNEL_TOKEN 추출)
if [ -f .env ]; then
    # export를 사용하여 변수로 가져오기
    export $(grep -v '^#' .env | xargs)
else
    echo ".env 파일이 존재하지 않습니다."
    exit 1
fi

if [ -z "$TUNNEL_TOKEN" ]; then
    echo "TUNNEL_TOKEN이 .env 파일에 설정되어 있지 않습니다."
    exit 1
fi

# 2. 필수 패키지 설치
apt-get update
apt-get install -y curl sudo tmux

# 3. cloudflared 설치 여부 확인 및 설치
if ! command -v cloudflared &> /dev/null; then
    echo "cloudflared 설치 중..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
    sudo dpkg -i cloudflared.deb
    rm cloudflared.deb
else
    echo "cloudflared가 이미 설치되어 있습니다."
fi

# 4. tmux 세션 관리
# 기존에 같은 이름의 세션이 있으면 종료 (재시작용)
tmux kill-session -t cf-tunnel 2>/dev/null

# 새로운 tmux 세션을 '데몬(백그라운드)'으로 생성하고 터널 실행
echo "Cloudflare Tunnel을 tmux(cf-tunnel) 세션에서 실행합니다."
tmux new-session -d -s cf-tunnel "cloudflared tunnel run --token $TUNNEL_TOKEN"

echo "설정 완료! 'tmux attach -t cf-tunnel' 명령어로 로그를 확인할 수 있습니다."