"""查询策略自动选择（纯规则，无 LLM）。"""

from __future__ import annotations

from app.knowledge.query_optimizer import select_query_strategy


def test_colloquial_short_uses_rewrite_hyde() -> None:
    assert select_query_strategy("西安有啥好玩的地儿") == "rewrite_hyde"


def test_recommend_uses_full() -> None:
    assert select_query_strategy("推荐西安旅游攻略") == "full"


def test_short_formal_uses_hyde() -> None:
    assert select_query_strategy("西安亲子景点") == "hyde"


def test_long_query_uses_multi_query() -> None:
    q = (
        "我想详细了解一下西安市区内适合家庭出游的历史文化类景点，"
        "包括开放时间、门票价格、地铁公交交通方式以及周边餐饮住宿建议"
    )
    assert len(q) > 45
    assert select_query_strategy(q) == "multi_query"
