from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import google.generativeai as genai


@lru_cache(maxsize=1)
def configure_gemini() -> None:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Do not raise at import time; allow running non-AI endpoints without configuration
        return
    genai.configure(api_key=api_key)


def get_gemini_model(model_name: str = "gemini-2.5-flash") -> Any:
    configure_gemini()
    # Defer import to runtime; this keeps startup flexible
    return genai.GenerativeModel(model_name)


__all__ = ["configure_gemini", "get_gemini_model"]


