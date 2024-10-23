from typing import Dict

def get_override_param(should_override: bool) -> Dict:
    return {"override": "true" if should_override else "false"}
