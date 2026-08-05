import yaml

def load_prompt(path):
    """Load simple template files (returns string)"""
    with open(path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
        # If it's a dict with "template" key, extract it
        return content["template"] if isinstance(content, dict) else content

def load_prompt_config(path):
    """Load complex prompt configs with system + template (returns dict)"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

"""
Addition to src/chains/prompt_loader.py — append this function to the
existing file (keep whatever load_prompt()/other functions are already there).
"""

from functools import lru_cache
from pathlib import Path



SYNTHESIS_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "synthesis.yaml"


@lru_cache
def load_synthesis_prompts() -> dict:
    """Load the composable synthesis prompt template (base + audience + structure + language)."""
    with SYNTHESIS_PROMPTS_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)