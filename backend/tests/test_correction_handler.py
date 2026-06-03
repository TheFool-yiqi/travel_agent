"""correction_handler 测试（P3.2）"""

from app.graph.semantic.correction_handler import detect_user_correction


def test_correction_bu_dui_shi_chengde():
    pending = {"slot": "destination", "candidate": "成都", "original": "程度"}
    corr = detect_user_correction("不对，是承德", {}, pending)
    assert corr is not None
    assert corr.value == "承德"
    assert corr.slot == "destination"


def test_correction_gai_cheng():
    corr = detect_user_correction("改成杭州", {"destination": "成都"}, None)
    assert corr is not None
    assert corr.value == "杭州"
    assert corr.slot == "destination"


def test_correction_destination_explicit():
    corr = detect_user_correction("目的地改成大理", {}, None)
    assert corr is not None
    assert corr.value == "大理"


def test_no_correction_normal():
    assert detect_user_correction("成都", {}, None) is None


def test_correction_departure_date() -> None:
    """TC-SEM-016: 日期改到 7 月 1 日."""
    corr = detect_user_correction("日期改到 7 月 1 日", {"departure_date": "2026-06-19"})
    assert corr is not None
    assert corr.slot == "departure_date"
    assert corr.value.endswith("-07-01")


def test_correction_departure_city_only():
    corr = detect_user_correction("出发地改成南京", {"destination": "北京", "departure_city": "上海"}, None)
    assert corr is not None
    assert corr.slot == "departure_city"
    assert corr.value == "南京"
