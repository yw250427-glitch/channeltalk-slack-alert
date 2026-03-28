"""
대화 내용 분석 모듈
채널톡 메시지에서 에스컬레이션 필요 여부와 심각도를 판단합니다.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── 키워드 사전 ────────────────────────────────────────────────
CRITICAL_KEYWORDS = [
    "소송", "고소", "고발", "변호사", "법적 조치", "법원", "공정위",
    "언론", "뉴스", "방송", "기자", "제보", "SNS 올릴", "유튜브",
    "사기", "사기꾼", "환불 거부", "소비자원", "신고"
]

ESCALATION_KEYWORDS = [
    "매니저", "팀장", "대표", "책임자", "상위", "윗분", "윗사람",
    "담당자 바꿔", "다른 사람", "상급자", "관리자", "임원"
]

NEGATIVE_KEYWORDS = [
    "환불", "취소", "해지", "이중 청구", "중복 결제", "오류", "버그",
    "안 됩니다", "안됩니다", "안돼요", "안되네요", "불량", "불편",
    "최악", "형편없", "엉망", "실망", "화납니다", "화나요",
    "짜증", "어이없", "황당", "열받", "미치겠", "못 쓰겠",
    "해지할", "탈퇴", "쓰지 않겠", "다른 서비스", "경쟁사"
]

REPEAT_COMPLAINT_THRESHOLD = 3   # 같은 대화에서 부정 키워드 N회 이상 → 반복 민원
CRITICAL_SCORE = 50   # 법적 위협 키워드 1건(50점)만으로도 CRITICAL
ESCALATION_SCORE = 30


@dataclass
class AnalysisResult:
    should_alert: bool
    severity: str                        # "critical" | "high" | "medium"
    score: int
    detected_keywords: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    summary: Optional[str] = None


def analyze(message_text: str, conversation_history: list[str] = None) -> AnalysisResult:
    """
    메시지(+ 대화 히스토리)를 분석해 에스컬레이션 여부를 판단합니다.

    Args:
        message_text: 최신 메시지 텍스트
        conversation_history: 이전 메시지 목록 (선택)

    Returns:
        AnalysisResult
    """
    score = 0
    detected = []
    reasons = []

    # 전체 분석 대상 텍스트 (최신 + 히스토리)
    all_text = message_text
    if conversation_history:
        all_text = " ".join(conversation_history) + " " + message_text

    lower = all_text.lower()

    # 1. 법적/언론 위협 (최우선 — 점수 50)
    for kw in CRITICAL_KEYWORDS:
        if kw in all_text:
            score += 50
            detected.append(kw)
            reasons.append(f"🚨 법적/공론화 위협 키워드 감지: '{kw}'")

    # 2. 에스컬레이션 요청 (점수 30)
    for kw in ESCALATION_KEYWORDS:
        if kw in all_text:
            score += 30
            detected.append(kw)
            reasons.append(f"⬆️ 상위 담당자 요청: '{kw}'")

    # 3. 부정 키워드 누적 (키워드당 10점)
    neg_count = 0
    for kw in NEGATIVE_KEYWORDS:
        if kw in all_text:
            neg_count += 1
            detected.append(kw)
            score += 10

    if neg_count >= REPEAT_COMPLAINT_THRESHOLD:
        reasons.append(f"🔁 반복 부정 키워드 {neg_count}회 감지 (반복 민원 의심)")
    elif neg_count > 0:
        reasons.append(f"😠 부정 키워드 {neg_count}건 감지")

    # 4. 심각도 분류
    if score >= CRITICAL_SCORE:
        severity = "critical"
        should_alert = True
    elif score >= ESCALATION_SCORE:
        severity = "high"
        should_alert = True
    elif score >= 20:
        severity = "medium"
        should_alert = True
    else:
        severity = "low"
        should_alert = False

    # 5. 요약문 생성
    summary = None
    if should_alert:
        preview = message_text[:80] + ("..." if len(message_text) > 80 else "")
        summary = f"'{preview}'"

    return AnalysisResult(
        should_alert=should_alert,
        severity=severity,
        score=score,
        detected_keywords=list(set(detected)),
        reasons=reasons,
        summary=summary,
    )
