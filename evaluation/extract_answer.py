import re

def extract_direct_answer(text):
    pattern = r"## Direct Answer\s*(.*?)\n---"

    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()

    return text.strip()