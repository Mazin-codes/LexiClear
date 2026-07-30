from config import LLM_PROVIDER

if LLM_PROVIDER == "groq":
    from rag.providers.groq_provider import generate

elif LLM_PROVIDER == "gemini":
    from rag.providers.gemini_provider import generate
else:

    raise ValueError(

        f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}"

    )