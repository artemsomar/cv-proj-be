from google import genai


class GeminiClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key) if api_key else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def generate(self, prompt: str) -> str:
        if self._client is None:
            return ""

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return (response.text or "").strip()
