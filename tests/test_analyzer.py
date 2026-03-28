"""
analyzer.py 단위 테스트
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analyzer import analyze


def test_no_issue():
    result = analyze("감사합니다. 잘 사용하고 있어요!")
    assert not result.should_alert
    assert result.severity == "low"


def test_legal_threat():
    result = analyze("이거 해결 안 해주면 소송 걸겠습니다.")
    assert result.should_alert
    assert result.severity == "critical"
    assert "소송" in result.detected_keywords


def test_escalation_request():
    result = analyze("담당자 말고 매니저나 팀장 연결해 주세요.")
    assert result.should_alert
    assert result.severity in ("high", "critical")


def test_repeat_complaints():
    result = analyze(
        "환불 안 되고 오류 계속 나고 짜증납니다. 해지할 거예요.",
        conversation_history=["어제도 버그 있었고 불편했어요."]
    )
    assert result.should_alert
    assert result.score >= 40


def test_media_threat():
    result = analyze("SNS 올릴 거고 언론에도 제보할 거예요.")
    assert result.should_alert
    assert result.severity == "critical"


def test_summary_generated():
    result = analyze("환불 안 해주면 소비자원에 신고할 거예요!")
    assert result.summary is not None
    assert result.should_alert
