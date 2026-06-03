"""chat_stream semantic trace 写入测试（P1.5）"""

from app.graph.semantic.frame import SemanticFrame, TextCorrection


def test_semantic_trace_serializable_for_extra_info():
    frame = SemanticFrame(
        normalized_text="程度",
        corrections=[
            TextCorrection(
                original="程度",
                corrected="成都",
                reason="typo_confirm",
                confidence=0.88,
            ),
        ],
        slot_updates={},
        guidance_step="destination",
        confidence=0.88,
        extraction_source="fuzzy",
    )
    trace = frame.to_trace()
    extra = {"semantic": trace}
    assert extra["semantic"]["corrections"][0]["corrected"] == "成都"
    assert extra["semantic"]["guidance_step"] == "destination"
