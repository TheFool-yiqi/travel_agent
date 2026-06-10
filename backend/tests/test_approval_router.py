"""approval_router keyword detection tests."""

from app.graph.routers.approval_router import user_wants_approval, user_wants_revision


def test_user_wants_approval_keywords() -> None:
    assert user_wants_approval("确认行程")
    assert user_wants_approval("OK 可以")
    assert not user_wants_approval("我想改一下")


def test_user_wants_revision_keywords() -> None:
    assert user_wants_revision("修改第二天")
    assert user_wants_revision("change hotel")
    assert not user_wants_revision("确认")


def test_revision_and_approval_can_both_match_mixed_phrase() -> None:
    assert user_wants_revision("确认但改酒店")
    assert user_wants_approval("确认但改酒店")
