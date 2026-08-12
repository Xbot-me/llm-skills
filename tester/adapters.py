"""Thin, uniform wrappers around each provider's SDK.

Every adapter exposes the same signature:
    call(model: str, system_prompt: str, user_prompt: str) -> str

Add a new provider by writing one function and registering it in ADAPTERS.
"""

import os


def call_anthropic(model: str, system_prompt: str, user_prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def call_gemini(model: str, system_prompt: str, user_prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text or ""


def call_groq(model: str, system_prompt: str, user_prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


ADAPTERS = {
    "anthropic": call_anthropic,
    "gemini": call_gemini,
    "groq": call_groq,
}


def call_model(provider: str, model: str, system_prompt: str, user_prompt: str) -> str:
    if provider not in ADAPTERS:
        raise ValueError(
            f"Unknown provider '{provider}'. Known providers: {list(ADAPTERS)}. "
            f"Add a new one in tester/adapters.py."
        )
    return ADAPTERS[provider](model, system_prompt, user_prompt)
