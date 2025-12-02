from typing import Dict, Any
# Baseline rule-based predictor
def baseline_predict(inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Very simple heuristics: base yield depends on crop
    crop = inputs.get("crop", "rice").lower()
    base = {"rice": 3000.0, "wheat": 2500.0, "maize": 2000.0}.get(crop, 1500.0)
    # Reduce yield for low nitrogen (if provided)
    n = inputs.get("n")
    if n is not None:
        if n < 0.2:
            base *= 0.7
        elif n < 0.5:
            base *= 0.9
    # simple recommendation
    rec = "Apply recommended fertilizer according to soil test. Ensure irrigation in dry spells."
    return {
        "predicted_yield": round(base, 2),
        "confidence": 0.6,
        "recommendation": rec
    }
