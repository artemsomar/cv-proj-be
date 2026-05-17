import json

from app.features.ai.client import GeminiClient
from app.features.ai.dto import RouteNarrationInput
from app.features.ai.prompts import (
    ROUTE_INSTRUCTIONS_SYSTEM_PROMPT,
    ROUTE_SYSTEM_PROMPT,
    build_route_instructions_user_prompt,
    build_route_user_prompt,
)


class AIRouteNarrationService:
    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    async def build_route_instructions(self, payload: RouteNarrationInput) -> str:
        if not payload.vertices:
            return "Маршрут не знайдено."

        if not self._client.enabled:
            return self._fallback(payload)

        user_prompt = build_route_user_prompt(
            heading_degrees=payload.heading_degrees,
            total_distance=payload.total_distance,
            vertices=payload.vertices,
            segments=payload.segments,
        )
        prompt = f"{ROUTE_SYSTEM_PROMPT}\n\n{user_prompt}"
        answer = await self._client.generate(prompt)
        return answer or self._fallback(payload)

    async def build_route_instructions_list(self, payload: RouteNarrationInput) -> list[str]:
        if not payload.vertices:
            return ["Маршрут не знайдено."]

        if not self._client.enabled:
            return self._fallback_list(payload)

        user_prompt = build_route_instructions_user_prompt(
            heading_degrees=payload.heading_degrees,
            total_distance=payload.total_distance,
            vertices=payload.vertices,
            segments=payload.segments,
        )
        prompt = f"{ROUTE_INSTRUCTIONS_SYSTEM_PROMPT}\n\n{user_prompt}"
        raw = await self._client.generate(prompt)
        return self._parse_instructions(raw) if raw else self._fallback_list(payload)

    @staticmethod
    def _parse_instructions(raw: str) -> list[str]:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            return [raw.strip()]
        try:
            steps = json.loads(raw[start:end])
            if isinstance(steps, list):
                return [str(s) for s in steps if s]
        except json.JSONDecodeError:
            pass
        return [raw.strip()]

    @staticmethod
    def _fallback(payload: RouteNarrationInput) -> str:
        if len(payload.vertices) == 1:
            return "Ви вже в точці призначення."
        last_vertex = payload.vertices[-1]
        return (
            f"Рухайтесь за маршрутом із {len(payload.vertices)} точок "
            f"приблизно {payload.total_distance:.0f} м. "
            f"Початковий напрямок: {payload.heading_degrees:.0f}°. "
            f"Кінцева вершина: {last_vertex['id']} на поверсі {last_vertex['floor']}."
        )

    @staticmethod
    def _fallback_list(payload: RouteNarrationInput) -> list[str]:
        if len(payload.vertices) == 1:
            return ["Ви вже в точці призначення."]
        last_vertex = payload.vertices[-1]
        return [
            f"Рухайтесь за маршрутом із {len(payload.vertices)} точок приблизно {payload.total_distance:.0f} м.",
            f"Початковий напрямок: {payload.heading_degrees:.0f}°.",
            f"Кінцева вершина: {last_vertex['id']} на поверсі {last_vertex['floor']}.",
        ]
