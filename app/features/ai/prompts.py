_BASE_DIRECTIONS_RULES = (
    "You are an indoor navigation assistant for a university building. "
    "Your answer must be in Ukrainian. "
    "Focus ONLY on spatial orientation: which room to exit, which direction to go (left, right, straight), "
    "which rooms or areas to pass through, and when to use stairs (up or down). "
    "NEVER mention distances in meters, walking time, or any numeric measurements. "
    "Use room names or numbers as landmarks whenever available. "
    "Do not mention raw graph vertex IDs unless no room name is available. "
    "Avoid inventing landmarks that are not present in metadata."
)

ROUTE_SYSTEM_PROMPT = _BASE_DIRECTIONS_RULES

ROUTE_INSTRUCTIONS_SYSTEM_PROMPT = (
    _BASE_DIRECTIONS_RULES + " "
    "Return ONLY a valid JSON array of strings, where each element is one step. "
    "Example: [\"Вийдіть з аудиторії 101 і поверніть ліворуч.\", \"Пройдіть повз аудиторії 102 і 103.\", \"Піднімайтесь по сходах на другий поверх.\", \"Ви прибули до аудиторії 201.\"] "
    "Do not include any text outside the JSON array."
)


def build_route_user_prompt(
    *, heading_degrees: float, total_distance: float, vertices: list[dict], segments: list[dict]
) -> str:
    return (
        f"The user is currently facing {heading_degrees:.1f} degrees.\n"
        "The route is provided as ordered vertices and segment-level movement data.\n"
        "Describe where to go, which rooms to pass, when to turn left or right, and when to change floors.\n"
        "If floors change between vertices, explicitly explain that transition.\n\n"
        f"Ordered vertices:\n{vertices}\n\n"
        f"Route segments:\n{segments}"
    )


def build_route_instructions_user_prompt(
    *, heading_degrees: float, total_distance: float, vertices: list[dict], segments: list[dict]
) -> str:
    return (
        f"The user is currently facing {heading_degrees:.1f} degrees.\n"
        "The route is provided as ordered vertices and segment-level movement data.\n"
        "Break the directions into individual steps. Each step is one action: exit a room, turn, pass through an area, change floor, or arrive.\n"
        "If floors change between vertices, make it a separate step.\n\n"
        f"Ordered vertices:\n{vertices}\n\n"
        f"Route segments:\n{segments}"
    )
