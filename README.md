# 📣 채널톡 → Slack 에스컬레이션 알림 봇

채널톡 고객 상담 중 **문제 상담** 또는 **상위 부서 보고가 필요한 대화**를 자동 감지하여 Slack으로 즉시 알림을 전송하는 시스템입니다.

---

## 🔍 감지 기준

| 분류 | 키워드 예시 | 점수 |
|------|------------|------|
| 🚨 법적·공론화 위협 | 소송, 고소, 언론, 공정위, 변호사 | +50 |
| ⬆️ 에스컬레이션 요청 | 매니저, 팀장, 책임자, 상위 담당자 | +30 |
| 😠 부정 키워드 누적 | 환불, 이중청구, 해지, 짜증, 최악 등 | +10/건 |

**심각도 분류**
- 🚨 `CRITICAL` — 70점 이상 (즉시 처리)
- 🔴 `HIGH` — 40~69점 (에스컬레이션 권고)
- 🟡 `MEDIUM` — 20~39점 (모니터링)

---

## 🚀 빠른 시작

### 1. 레포지토리 클론

```bash
git clone https://github.com/YOUR_USERNAME/channeltalk-slack-alert.git
cd channeltalk-slack-alert
```

### 2. 가상환경 & 의존성 설치

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 아래 값 입력
```

| 변수 | 설명 | 발급 위치 |
|------|------|----------|
| `SLACK_BOT_TOKEN` | `xoxb-`로 시작하는 Slack Bot Token | [api.slack.com/apps](https://api.slack.com/apps) |
| `SLACK_ALERT_CHANNEL` | 알림 수신 채널 (예: `#cs-escalation`) | Slack 채널 설정 |
| `CHANNELTALK_WEBHOOK_SECRET` | Webhook 서명 검증 Secret | 채널톡 → 개발자 도구 → Webhook |

### 4. 서버 실행

```bash
python app.py
```

### 5. 테스트

```bash
pytest tests/ -v
```

---

## ⚙️ Slack Bot 설정

1. [api.slack.com/apps](https://api.slack.com/apps) → **Create New App**
2. **OAuth & Permissions** → Bot Token Scopes 추가:
   - `chat:write`
   - `chat:write.public`
3. **Install to Workspace** → Bot Token(`xoxb-...`) 복사
4. 알림 받을 채널에 Bot 초대: `/invite @봇이름`

---

## ⚙️ 채널톡 Webhook 설정

1. 채널톡 관리자 → **개발자 도구** → **Webhook**
2. URL: `https://YOUR_SERVER_URL/webhook/channeltalk`
3. 이벤트: `message_created` 체크
4. Webhook Secret 복사 → `.env`의 `CHANNELTALK_WEBHOOK_SECRET`에 입력

---

## 🌐 배포 (Render / Railway / Fly.io)

```bash
# Render: render.yaml 또는 Procfile 자동 감지
# 환경 변수를 대시보드에서 직접 설정

web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

---

## 📡 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/webhook/channeltalk` | 채널톡 Webhook 수신 |
| `GET`  | `/health` | 헬스체크 |

---

## 📂 프로젝트 구조

```
channeltalk-slack-alert/
├── app.py              # Flask Webhook 서버
├── analyzer.py         # 대화 분석 로직 (키워드 점수화)
├── slack_bot.py        # Slack Block Kit 알림 전송
├── requirements.txt
├── Procfile            # 배포용
├── .env.example        # 환경 변수 템플릿
├── .gitignore
├── tests/
│   └── test_analyzer.py
└── .github/
    └── workflows/
        └── ci.yml      # GitHub Actions CI
```

---

## 🔔 Slack 알림 예시

```
🚨 CS 에스컬레이션 알림 — 즉시 처리 필요

고객명: 홍길동          심각도: 🚨 CRITICAL (점수: 80)
대화 ID: abc-123        채널: 채팅

💬 최근 메시지
'환불 안 해주면 소비자원에 신고하고 언론에 제보할 거예요.'

📋 감지 이유
• 🚨 법적/공론화 위협 키워드 감지: '소비자원'
• 🚨 법적/공론화 위협 키워드 감지: '언론'
• 🔁 반복 부정 키워드 4회 감지 (반복 민원 의심)

🔑 감지 키워드
`소비자원`  `언론`  `환불`  `신고`

[💬 채널톡 대화 보기]
```
