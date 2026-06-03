"""需求收集回复校验与模板追问"""

from datetime import date

from app.graph.templates.collect_followup import render_collect_followup
from app.graph.validators.collect_reply import (
    sanitize_collect_reply,
    should_mention_annual_leave,
    strip_markdown_bold_artifacts,
    validate_collect_reply,
)


def test_strip_markdown_bold_artifacts():
    raw = "那我们来聊聊时间吧——**你大概什么时候出发"
    cleaned = strip_markdown_bold_artifacts(raw)
    assert "**" not in cleaned
    assert "你大概什么时候出发" in cleaned


def test_validate_requires_holiday_when_asking_date():
    reply = "你大概什么时候出发？比如本周末？"
    errors = validate_collect_reply(reply, missing_departure_date=True)
    assert any("节假日" in e for e in errors)


def test_sanitize_fixes_short_trip_21_nights():
    raw = "还有，你计划玩几天呢短途21晚，还是想休个年假来个4-5天的"
    cleaned = sanitize_collect_reply(raw, dialogue_text="上海")
    assert "21" not in cleaned
    assert "2-3天" in cleaned or "4-5" in cleaned


def test_validate_rejects_annual_leave_in_june():
    reply = "打算请年假出去玩吗？还是这周末出发？"
    errors = validate_collect_reply(reply, dialogue_text="上海")
    assert any("年假" in e for e in errors)


def test_should_not_mention_annual_leave_in_june():
    assert should_mention_annual_leave("", anchor=date(2026, 6, 1)) is False


def test_should_mention_annual_leave_when_user_said_so():
    assert should_mention_annual_leave("我想用年假", anchor=date(2026, 6, 1)) is True


def test_render_collect_followup_shanghai_missing_date_and_days():
    fields = {"departure_city": "上海", "destination": "成都"}
    text = render_collect_followup(fields)
    assert "成都" in text or "上海" in text
    assert "端午" in text or "本周末" in text

    fields_with_date = {
        "departure_city": "上海",
        "destination": "成都",
        "departure_date": "2026-06-19",
    }
    days_text = render_collect_followup(fields_with_date)
    assert "2-3 天" in days_text
