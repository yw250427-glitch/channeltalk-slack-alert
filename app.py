"""
채널톡 → Slack 에스컬레이션 알림 서버
채널톡 Webhook 이벤트를 수신하여 문제 상담을 감지하면 Slack으로 즉시 알립니다.
"""

import os
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from analyzer import analyze
from slack_bot import send_alert

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CHANNELTALK_WEBHOOK_SECRET = os.environ.get("CHANNELTALK_WEBHOOK_SECRET", "")


# ── 서명 검증 ────────────────────────────────────────────────
def verify_channeltalk_signature(payload: bytes, signature: str) -> bool:
    """채널톡 Webhook 서명을 검증합니다."""
    if not CHANNELTALK_WEBHOOK_SECRET:
        logger.warning("CHANNELTALK_WEBHOOK_SECRET이 미설정 — 서명 검증 건너뜀")
        return True
    expected = hmac.new(
        CHANNELTALK_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── 유틸 ─────────────────────────────────────────────────────
def build_channel_url(channel_id: str, conversation_id: str) -> str:
    return f"https://desk.channel.io/#/channels/{channel_id}/user-chats/{conversation_id}"


# ── Webhook 엔드포인트 ─────────────────────────────────────────
@app.route("/webhook/channeltalk", methods=["POST"])
def channeltalk_webhook():
    # 1. 서명 검증
    sig = request.headers.get("X-Signature-256", "")
    if not verify_channeltalk_signature(request.data, sig):
        logger.warning("서명 검증 실패")
        return jsonify({"error": "invalid signature"}), 401

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "invalid payload"}), 400

    event_type = payload.get("event") or payload.get("type", "")
    logger.info(f"이벤트 수신: {event_type}")

    # 2. 메시지 이벤트만 처리
    if event_type not in ("message_created", "userMessage", "message"):
        return jsonify({"status": "ignored", "event": event_type}), 200

    # 3. 필드 추출 (채널톡 Webhook 포맷)
    entity = payload.get("entity", payload)
    message_text = (
        entity.get("plainText")
        or entity.get("text")
        or entity.get("message", "")
    )
    if not message_text:
        return jsonify({"status": "empty_message"}), 200

    conversation_id = (
        entity.get("chatId")
        or entity.get("conversationId")
        or entity.get("id", "unknown")
    )
    channel_id = entity.get("channelId", "")
    customer_name = (
        payload.get("refers", {}).get("user", {}).get("name")
        or entity.get("personName")
        or "알 수 없음"
    )

    # 대화 히스토리 (있으면 함께 분석)
    history = [
        m.get("plainText", "")
        for m in payload.get("history", [])
        if m.get("plainText")
    ]

    # 4. 분석
    result = analyze(message_text, history)
    logger.info(
        f"분석 완료 — 고객: {customer_name} | 점수: {result.score} | "
        f"심각도: {result.severity} | 알림: {result.should_alert}"
    )

    # 5. 알림 전송
    if result.should_alert:
        channel_url = build_channel_url(channel_id, conversation_id)
        sent = send_alert(
            result=result,
            customer_name=customer_name,
            conversation_id=conversation_id,
            channel_url=channel_url,
        )
        return jsonify({
            "status": "alert_sent" if sent else "alert_failed",
            "severity": result.severity,
            "score": result.score,
        }), 200

    return jsonify({"status": "ok", "score": result.score}), 200


# ── 헬스체크 ─────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "channeltalk-slack-alert"}), 200


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "CS 에스컬레이션 알림 서버",
        "webhook": "/webhook/channeltalk",
        "health": "/health",
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"서버 시작 — port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
