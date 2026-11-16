# =============================================================
# utils/llm_config.py
# Configures the Groq LLM via LangChain
# =============================================================

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables from the .env file
load_dotenv()


def get_llm(temperature: float = 0.7) -> ChatGroq:
    """
    Create and return a configured Groq LLM instance.

    Uses Llama 3.3 70B Versatile — a powerful, free model via Groq.

    Args:
        temperature (float): Controls creativity/randomness.
                             0.0 = deterministic, 1.0 = creative.

    Returns:
        ChatGroq: A LangChain-compatible Groq LLM instance.

    Raises:
        ValueError: If GROQ_API_KEY is not set in the environment.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Please add your key to the .env file. "
            "Get a free key at https://console.groq.com"
        )

    # Initialize the ChatGroq model
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",  # Best free model on Groq
        temperature=temperature,           # Creativity level
        api_key=api_key,                   # Loaded from .env
        max_tokens=2048,                   # Max response length
    )

    return llm


def validate_api_key() -> tuple[bool, str]:
    """
    Check if the Groq API key is configured correctly.

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return False, "GROQ_API_KEY not found in environment variables."

    if api_key == "your_groq_api_key_here":
        return False, "Please replace the placeholder with your actual Groq API key."

    if len(api_key) < 20:
        return False, "API key seems too short. Please verify it."

    return True, "API key is configured."
