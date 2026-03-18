#!/bin/bash

# --- 색상 설정 (터미널에서 예쁘게 보이도록) ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}🚀 Edge AI Backend - Git Workflow Manager 🚀${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# 대화형 메뉴 설정
PS3=$'\n작업할 항목을 선택하세요 (번호 입력): '
options=(
    "작업 시작: MQTT Worker (디바이스 신호 처리)" 
    "작업 시작: API Server (Presigned URL 발급)" 
    "전체 보기: Dev 브랜치로 이동 및 Sparse 해제" 
    "저장소 반영: 현재 상태 커밋 및 푸시" 
    "종료"
)

select opt in "${options[@]}"
do
    case $opt in
        "작업 시작: MQTT Worker (디바이스 신호 처리)")
            BRANCH_NAME="feature/v1/mqtt"
            echo -e "\n${YELLOW}>> 1. '$BRANCH_NAME' 브랜치를 준비합니다...${NC}"
            # dev 브랜치에서 파생하여 이동 (이미 있으면 해당 브랜치로 이동)
            git checkout -B $BRANCH_NAME dev
            
            echo -e "${YELLOW}>> 2. 관심사 분리 (Sparse-checkout) 적용 중...${NC}"
            git sparse-checkout init --cone
            git sparse-checkout set core apps/mqtt_worker .specify specs .github git-control.sh
            
            echo -e "${GREEN}✅ 세팅 완료! 탐색기에는 core와 mqtt_worker 폴더만 표시됩니다.${NC}"
            break
            ;;

        "작업 시작: API Server (Presigned URL 발급)")
            BRANCH_NAME="feature/v1/api"
            echo -e "\n${YELLOW}>> 1. '$BRANCH_NAME' 브랜치를 준비합니다...${NC}"
            git checkout -B $BRANCH_NAME dev
            
            echo -e "${YELLOW}>> 2. 관심사 분리 (Sparse-checkout) 적용 중...${NC}"
            git sparse-checkout init --cone
            git sparse-checkout set core apps/api_server .specify specs .github git-control.sh
            
            echo -e "${GREEN}✅ 세팅 완료! 탐색기에는 core와 api_server 폴더만 표시됩니다.${NC}"
            break
            ;;

        "전체 보기: Dev 브랜치로 이동 및 Sparse 해제")
            echo -e "\n${YELLOW}>> 1. 'dev' 브랜치로 이동합니다...${NC}"
            git checkout dev
            
            echo -e "${YELLOW}>> 2. Sparse-checkout을 해제하여 모든 폴더를 복구합니다...${NC}"
            git sparse-checkout disable
            
            echo -e "${GREEN}✅ 세팅 완료! 모든 모듈이 표시됩니다.${NC}"
            break
            ;;

        "저장소 반영: 현재 상태 커밋 및 푸시")
            CURRENT_BRANCH=$(git branch --show-current)
            echo -e "\n${CYAN}[현재 브랜치: $CURRENT_BRANCH]${NC}"
            
            # 변경된 파일 목록을 짧게 보여줌
            git status -s
            echo ""
            
            # 커밋 메시지 입력받기
            read -p "📝 커밋 메시지를 입력하세요 (취소하려면 그냥 Enter): " commit_msg
            
            if [ -z "$commit_msg" ]; then
                echo -e "${YELLOW}취소되었습니다.${NC}"
            else
                git add .
                git commit -m "$commit_msg"
                # 원격 브랜치가 없으면 새로 만들면서 푸시 (-u)
                git push -u origin $CURRENT_BRANCH
                echo -e "${GREEN}✅ 커밋 및 푸시가 성공적으로 완료되었습니다!${NC}"
            fi
            break
            ;;

        "종료")
            echo "스크립트를 종료합니다. 화이팅!"
            break
            ;;

        *) 
            echo "잘못된 선택입니다. 1~5 사이의 번호를 입력해주세요."
            ;;
    esac
done