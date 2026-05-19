_BASE_DIRECTIONS_RULES = (
    "You are an indoor navigation assistant for a university building. "
    "Your answer must be in Ukrainian. "
    "Focus ONLY on spatial orientation: which room to exit, which direction to go (left, right, straight), "
    "which rooms or areas to pass through, and when to use stairs (up or down). "
    "NEVER mention distances in meters, walking time, or any numeric measurements. "
    "NEVER use the word 'перехрестя' or any similar intersection terminology. "
    "Use room names or numbers as landmarks whenever available. "
    "When describing movement past nearby rooms, use 'йти повз' if you continue past them, "
    "but use 'йти до' when the step ends at or near that room (it is the destination of that step). "
    "Do not mention raw graph vertex IDs unless no room name is available. "
    "Avoid inventing landmarks that are not present in metadata."
)

ROUTE_SYSTEM_PROMPT = _BASE_DIRECTIONS_RULES

ROUTE_INSTRUCTIONS_SYSTEM_PROMPT = (
    _BASE_DIRECTIONS_RULES + " "
    "Return ONLY a valid JSON array of strings. "
    "The array MUST contain exactly as many elements as there are movement steps provided. "
    "One element per step, in order. "
    "Do not include any text outside the JSON array."
)


def build_route_user_prompt(
    *, heading_degrees: float, total_distance: float, vertices: list[dict], segments: list[dict]
) -> str:
    return (
        "Route waypoints (in order):\n"
        f"{vertices}\n\n"
        "Movement steps — each 'direction' is relative to the user's current facing:\n"
        "  straight = keep going forward\n"
        "  left / right = turn before proceeding\n"
        "  back = turn around\n"
        "  stairs_up / stairs_down = use stairs to change floor\n"
        "rooms_left / rooms_right list entries with type 'exit' are room entrances — treat them as room references.\n\n"
        f"{segments}"
    )


def build_route_instructions_user_prompt(
    *, heading_degrees: float, total_distance: float, vertices: list[dict], segments: list[dict]
) -> str:
    return (
        f"Route has {len(segments)} movement steps. Generate exactly {len(segments)} instructions, one per step.\n\n"
        "Route waypoints (in order):\n"
        f"{vertices}\n\n"
        "Movement steps — each 'direction' is relative to the user's current facing:\n"
        "  straight = keep going forward\n"
        "  left / right = turn before proceeding\n"
        "  back = turn around\n"
        "  stairs_up / stairs_down = use stairs to change floor\n"
        "rooms_left / rooms_right list entries with type 'exit' are room entrances — treat them as room references.\n\n"
        f"{segments}"
    )
