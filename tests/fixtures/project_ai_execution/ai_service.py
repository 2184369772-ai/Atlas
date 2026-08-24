def build_ai_result_shape():
    return {
        "response_format": "json_object",
        "confidence": "medium",
        "risk_level": "high",
        "manual_required": True,
        "escalation_reasons": ["human review required"],
    }
