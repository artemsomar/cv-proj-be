_BASE_DIRECTIONS_RULES = (
    "You are an indoor navigation assistant for a university building. "
    "Your answer must be in Ukrainian. "
    "Focus ONLY on spatial orientation: which room to exit, which direction to go (left, right, straight), "
    "which rooms or areas to pass through, and when to use stairs (up or down). "
    "NEVER mention distances in meters, walking time, or any numeric measurements. "
    "NEVER use the word 'перехрестя' or any similar intersection terminology. "
    "Use room names or numbers as landmarks whenever available. "
    "When referencing nearby rooms, mention at most 2-3 of the most notable ones — do NOT list all of them. "
    "Describe rooms naturally in a sentence, never as a comma-separated enumeration. "
    "Always use second-person plural imperative forms: 'йдіть', 'поверніть', 'підніміться', 'спустіться', 'вийдіть' — never infinitives like 'йти', 'повернути'. "
    "Each step has a 'nearby_rooms' list and a 'direction' field. "
    "If direction is 'straight': mention 1-2 nearby_rooms naturally with their side — 'праворуч кімната X', 'ліворуч кімната Y'. "
    "If direction is a turn (left/right/back) or stairs: use nearby_rooms ONLY as a spatial anchor for where to turn — 'поверніть ліворуч біля X'. Do NOT mention sides. "
    "Each step may also have a 'destination' field — this is where the step physically ends. "
    "If 'destination' is set, add 'йдіть до [destination]' at the end — but ONLY if the destination was not already used as the turn anchor in the same instruction. "
    "Always properly decline Ukrainian nouns: 'до дверей', 'до аудиторії', 'біля дверей', never use nominative case after prepositions. "
    "nearby_rooms are passed along the way only — never use 'йдіть до' for them. "
    "When describing a turn, always reference a nearby landmark (room door, corridor end, etc.) to indicate WHERE to turn — never describe a turn without a spatial anchor. "
    "If the first waypoint has type 'room', the user is inside that room — the first instruction must be ONLY 'вийдіть з кімнати X', nothing else added. "
    "For all other waypoints, the user is in a corridor — NEVER say they are exiting or inside a room. "
    "Reference non-starting rooms only as corridor landmarks: 'біля дверей кімнати X', 'навпроти кімнати X'. "
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
