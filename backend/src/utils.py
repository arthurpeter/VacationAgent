import os
import json
import re
from typing import List, Dict, Any


def delete_file(path: str):
    """Delete the file at the specified path if it exists."""
    if os.path.exists(path):
        os.remove(path)


def ensure_dir_exists(path: str):
    """Ensure the directory for the given path exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def count_lines(path: str, encoding: str = 'utf-8') -> int:
    """Return the number of lines in a file."""
    with open(path, 'r', encoding=encoding) as f:
        return sum(1 for _ in f)


def read_text(path: str, encoding: str = 'utf-8') -> str:
    """Read the entire content of a file as a string."""
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def read_lines(path: str, encoding: str = 'utf-8') -> List[str]:
    """Read all lines from a file."""
    with open(path, 'r', encoding=encoding) as f:
        return f.readlines()


def read_json(path: str, encoding: str = 'utf-8') -> Dict:
    """Read a single JSON object from a file."""
    with open(path, 'r', encoding=encoding) as f:
        return json.load(f)


def read_jsons(path: str, encoding: str = 'utf-8') -> List[Dict]:
    """Read a list of JSON objects from a file."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    with open(path, 'r', encoding=encoding) as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Expected a JSON array at the top level.")
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON file: {e}")


def output_text(path: str, text: str, encoding: str = 'utf-8'):
    """Write a string to a file (overwrites existing content)."""
    ensure_dir_exists(path)
    with open(path, 'w', encoding=encoding) as f:
        f.write(text)


def output_lines(path: str, lines: List[str], encoding: str = 'utf-8'):
    """Write a list of lines to a file (overwrites existing content)."""
    ensure_dir_exists(path)
    with open(path, 'w', encoding=encoding) as f:
        f.writelines([line + '\n' if not line.endswith('\n') else line for line in lines])


def append_line(path: str, line: str, encoding: str = 'utf-8'):
    """Append a single line to a file."""
    ensure_dir_exists(path)
    with open(path, 'a', encoding=encoding) as f:
        f.write(line + '\n')


def append_lines(path: str, lines: List[str], encoding: str = 'utf-8'):
    """Append multiple lines to a file."""
    ensure_dir_exists(path)
    with open(path, 'a', encoding=encoding) as f:
        f.writelines([line + '\n' if not line.endswith('\n') else line for line in lines])


def output_json(path: str, data: Dict[str, Any], encoding: str = 'utf-8'):
    """Write a single JSON object to a file (overwrites existing content)."""
    ensure_dir_exists(path)
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def output_jsons(path: str, data: List[Dict[str, Any]], encoding: str = 'utf-8'):
    """Write a list of JSON objects to a file as a JSON array."""
    ensure_dir_exists(path)
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def append_json(path: str, data: Dict[str, Any], encoding: str = 'utf-8'):
    """Append a JSON object to a file (each JSON object on a new line)."""
    ensure_dir_exists(path)
    with open(path, 'a', encoding=encoding) as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False) + '\n')


def append_jsons(path: str, data: List[Dict[str, Any]], encoding: str = 'utf-8'):
    """Append a JSON object to a file (each JSON object on a new line)."""
    ensure_dir_exists(path)
    with open(path, 'a', encoding=encoding) as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False) + '\n')

def replace_value(destination: str, value: str) -> str:
    """Replace the section within the curly brackets (is applicable) with the value provided."""
    return re.sub(r"\{.*?\}", lambda _: "{" + value + "}", destination)


if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the utility functions.")