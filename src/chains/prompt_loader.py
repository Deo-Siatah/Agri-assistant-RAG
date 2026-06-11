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