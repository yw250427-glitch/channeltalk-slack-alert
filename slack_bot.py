"""
Slack 알림 모듈
분석 결과를 Slack 채널에 Block Kit 메시지로 전송합니다.
"""

import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from analyzer import AnalysisResult

logger = logging.getLogger(__name__)

SEVERITY_META = {
    "critical": {"emoji": "🚨", "color": "#FF0000", "label": "즉시 처리 필요"},
    "high":     {"emoji": "🔴", "color": "#FF6B35", "label": "에스컬레이션 권고"},
    "medium":   {"emoji": "🟡", "color": "#FFD166", "label": "모니터링 필요"},
}


def send_alert(
    result: AnalysisResult,
    customer_name: str,
    conversation_id: str,
    channel_url: str,
    channel_name: str = None,
) -> bool:
    """
    Slack 채널에 에스컬레이션 알림을 전송합니다.

    Returns:
        True if successful, False otherwise
    """
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_ALERT_CHANNEL", "#cs-escalation")

    if not token:
        logger.error("SLACK_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        return False

    client = WebClient(token=token)
    meta = SEVERITY_META.get(result.severity, SEVERITY_META["medium"])

    # ── Block Kit 메시지 구성 ──
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{meta['emoji']} CS 에스컬레이션 알림 — {meta['label']}",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*고객명*\n{customer_name}"},
                {"type": "mrkdwn", "text": f"*심각도*\n{meta['emoji']} `{result.severity.upper()}` (점수: {result.score})"},
                {"type": "mrkdwn", "text": f"*대화 ID*\n`{conversation_id}`"},
                {"type": "mrkdwn", "text": f"*채널*\n{channel_name or '채널톡'}"},
            ],
        },
    ]

    # 감지 내용 요약
    if result.summary:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*💬 최근 메시지*\n{result.summary}",
            },
        })

    # 감지된 이유 목록
    if result.reasons:
        reason_text = "\n".join(f"• {r}" for r in result.reasons)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📋 감지 이유*\n{reason_text}",
            },
        })

    # 감지 키워드
    if result.detected_keywords:
        kw_text = "  ".join(f"`{k}`" for k in result.detected_keywords[:10])
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🔑 감지 키워드*\n{kw_text}"},
        })

    # 액션 버튼
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "💬 채널톡 대화 보기", "emoji": True},
                "url": channel_url,
                "style": "primary",
            },
        ],
    })

    try:
        client.chat_postMessage(
            channel=channel,
            text=f"{meta['emoji']} CS 에스컬레이션 알림 | 고객: {customer_name} | {meta['label']}",
            blocks=blocks,
            attachments=[{"color": meta["color"], "fallback": f"CS 에스컬레이션: {customer_name}"}],
        )
        logger.info(f"Slack 알림 전송 완료 — {customer_name} / {result.severity}")
        return True

    except SlackApiError as e:
        logger.error(f"Slack 전송 실패: {e.response['error']}")
        return False
