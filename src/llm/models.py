"""Builds the Gemini chat model via LangChain.

`langchain-google-genai` auto-reads the API key from GEMINI_API_KEY (or
GOOGLE_API_KEY) env vars, so no key is passed explicitly.
"""
from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from .. import config


def build_chat_model(**kwargs) -> ChatGoogleGenerativeAI:
    params = {"model": config.MODEL_NAME, "temperature": 0}
    params.update(kwargs)
    return ChatGoogleGenerativeAI(**params)
