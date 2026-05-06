"""
SpeakSQL — LLM Provider implementations.
Supports Groq (free), HuggingFace, and Google Gemini.
"""


class LLMProvider:
    """Base class for LLM providers."""
    def call(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        raise NotImplementedError


class GroqProvider(LLMProvider):
    """Groq API provider — fast inference, generous free tier."""
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model

    def call(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            err = str(e).lower()
            if "authentication" in err or "api key" in err or "invalid" in err:
                raise RuntimeError("🔑 Invalid Groq API Key. Get a free key from https://console.groq.com/keys")
            elif "rate" in err or "429" in err:
                raise RuntimeError("⏳ Groq rate limit reached. Please wait and try again.")
            raise RuntimeError(f"Groq API error: {e}")


class HuggingFaceProvider(LLMProvider):
    """HuggingFace Inference API provider."""
    def __init__(self, api_key: str, model: str = "Qwen/Qwen2.5-Coder-32B-Instruct"):
        from huggingface_hub import InferenceClient
        self.client = InferenceClient(api_key=api_key)
        self.model = model

    def call(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=max(temperature, 0.01),
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            err = str(e).lower()
            if "unauthorized" in err or "401" in err:
                raise RuntimeError("🔑 Invalid HuggingFace Token. Get one from https://huggingface.co/settings/tokens")
            elif "rate" in err or "429" in err:
                raise RuntimeError("⏳ HuggingFace rate limit reached. Please wait and try again.")
            raise RuntimeError(f"HuggingFace API error: {e}")


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def call(self, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
        from google.genai import types
        try:
            resp = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return resp.text or ""
        except Exception as e:
            err = str(e).lower()
            if "api key not valid" in err or "invalid_argument" in err:
                raise RuntimeError("🔑 Invalid Google API Key. Get one from https://aistudio.google.com/apikey")
            elif "quota" in err or "429" in err or "resource_exhausted" in err:
                raise RuntimeError("⏳ Gemini quota exhausted. Try Groq (free, generous limits).")
            raise RuntimeError(f"Gemini API error: {e}")


def create_provider(provider_key: str, api_key: str, model: str) -> LLMProvider:
    """Factory function to create the right LLM provider."""
    providers = {
        "groq": GroqProvider,
        "huggingface": HuggingFaceProvider,
        "gemini": GeminiProvider,
    }
    cls = providers.get(provider_key)
    if not cls:
        raise ValueError(f"Unknown provider: {provider_key}")
    return cls(api_key=api_key, model=model)
