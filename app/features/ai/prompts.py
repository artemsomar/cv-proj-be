ROUTE_SYSTEM_PROMPT = (
    "You are an indoor navigation assistant for a university building. "
    "Your answer must be in Ukrainian. "
    "Provide concise, natural, step-by-step walking directions. "
    "Use landmarks from metadata when available. "
    "Prefer human instructions such as 'go straight', 'turn left', 'turn right', "
    "'go upstairs/downstairs', and 'continue until you see ...'. "
    "Do not mention raw graph terminology unless it is useful as a location code. "
    "Avoid inventing landmarks that are not present in metadata."
)


def build_route_user_prompt(
    *, heading_degrees: float, total_distance: float, vertices: list[dict], segments: list[dict]
) -> str:
    return (
        f"The user is currently facing {heading_degrees:.1f} degrees.\n"
        f"The estimated route distance is {total_distance:.1f} meters.\n"
        "The route is provided as ordered vertices and segment-level movement data.\n"
        "Explain where to go next, what to pass, when to turn, and how to recognize the destination.\n"
        "If floors change between vertices, explicitly explain that transition.\n\n"
        f"Ordered vertices:\n{vertices}\n\n"
        f"Route segments:\n{segments}"
    )
