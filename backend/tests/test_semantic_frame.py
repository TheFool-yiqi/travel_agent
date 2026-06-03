"""SemanticFrame 模型测试（P1.1）"""

from app.graph.semantic.frame import SemanticFrame, TextCorrection


def test_semantic_frame_to_trace():
    frame = SemanticFrame(
        normalized_text="成都",
        corrections=[
            TextCorrection(
                original="程度",
                corrected="成都",
                reason="typo_confirm",
                confidence=0.88,
            ),
        ],
        slot_updates={"destination": "成都"},
        guidance_step="destination",
        confidence=0.88,
        extraction_source="fuzzy",
    )
    trace = frame.to_trace()
    assert trace["normalized_text"] == "成都"
    assert trace["corrections"][0]["corrected"] == "成都"
    assert trace["slot_updates"]["destination"] == "成都"
    assert trace["confidence"] == 0.88
