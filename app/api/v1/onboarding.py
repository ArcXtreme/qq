from fastapi import APIRouter, Depends, Header
from typing import Optional
from app.core.auth import get_current_user
from app.i18n import translate
from app.models.models import User

router = APIRouter()

@router.get("/tips")
def onboarding_tips(
    accept_language: Optional[str] = Header(None, alias="Accept-Language"), 
    user: User = Depends(get_current_user)
):
    # Default to user preference, fallback to English
    lang = (user.language_preference or "en").lower()
    
    # Optional: Override with Accept-Language header if present
    if accept_language:
        # Extract primary language (e.g. "hi-IN" -> "hi")
        try:
            lang = accept_language.split(",")[0].split("-")[0].lower()
        except Exception:
            pass

    tips = [
        translate("tip.onboarding_1", lang),
        translate("tip.onboarding_2", lang),
        translate("tip.onboarding_3", lang),
    ]
    
    return {"tips": tips, "language": lang}
