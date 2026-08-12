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

def call_anthropic_with_tools(model: str, system_prompt: str, user_prompt: str, tools: list[dict], tool_executor) -> tuple[str, list[dict]]:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    anthropic_tools = [{
        "name": t["name"],
        "description": t["description"],
        "input_schema": t["parameters"]
    } for t in tools]

    messages = [{"role": "user", "content": user_prompt}]
    trace = []

    for _ in range(5):
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=anthropic_tools
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    trace.append({"tool": block.name, "kwargs": block.input})
                    result = tool_executor(block.name, block.input)
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        }]
                    })
        else:
            final_text = "".join(b.text for b in response.content if b.type == "text")
            return final_text, trace

    raise RuntimeError("Max tool turns exceeded")


def call_gemini_with_tools(model: str, system_prompt: str, user_prompt: str, tools: list[dict], tool_executor) -> tuple[str, list[dict]]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    gemini_tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["parameters"]
                )
            ]
        ) for t in tools
    ]

    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=gemini_tools
        )
    )

    trace = []
    response = chat.send_message(user_prompt)

    for _ in range(5):
        if response.function_calls:
            parts = []
            for fc in response.function_calls:
                kwargs = fc.args if isinstance(fc.args, dict) else dict(fc.args) if fc.args else {}
                trace.append({"tool": fc.name, "kwargs": kwargs})
                result = tool_executor(fc.name, kwargs)
                parts.append(types.Part.from_function_response(
                    name=fc.name,
                    response={"result": str(result)}
                ))
            response = chat.send_message(parts)
        else:
            return response.text or "", trace

    raise RuntimeError("Max tool turns exceeded")


def call_groq_with_tools(model: str, system_prompt: str, user_prompt: str, tools: list[dict], tool_executor) -> tuple[str, list[dict]]:
    import json
    from groq import Groq

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    groq_tools = [{"type": "function", "function": t} for t in tools]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    trace = []
    for _ in range(5):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=groq_tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                kwargs = json.loads(tc.function.arguments)
                trace.append({"tool": tc.function.name, "kwargs": kwargs})
                result = tool_executor(tc.function.name, kwargs)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": str(result)
                })
        else:
            return msg.content or "", trace

    raise RuntimeError("Max tool turns exceeded")


TOOL_ADAPTERS = {
    "anthropic": call_anthropic_with_tools,
    "gemini": call_gemini_with_tools,
    "groq": call_groq_with_tools,
}

def call_model_with_tools(provider: str, model: str, system_prompt: str, user_prompt: str, tools: list[dict], tool_executor) -> tuple[str, list[dict]]:
    if provider not in TOOL_ADAPTERS:
        raise ValueError(
            f"Unknown provider '{provider}' for tools. Known providers: {list(TOOL_ADAPTERS)}."
        )
    return TOOL_ADAPTERS[provider](model, system_prompt, user_prompt, tools, tool_executor)
