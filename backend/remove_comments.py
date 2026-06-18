import os
import tokenize
from io import StringIO


def remove_comments_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tokens = tokenize.generate_tokens(StringIO(source).readline)

        filtered_tokens = []
        for token in tokens:
            if token.type == tokenize.COMMENT:
                continue
            filtered_tokens.append(token)

        new_source = tokenize.untokenize(filtered_tokens)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_source)

        print(f"Processed: {filepath}")

    except Exception as e:
        print(f"Failed: {filepath} -> {e}")


def remove_comments_recursively(start_dir="."):
    for root, dirs, files in os.walk(start_dir):
        dirs[:] = [
            d
            for d in dirs
            if d not in {".git", "__pycache__", ".venv", "venv", "env", "alembic"}
        ]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                remove_comments_from_file(filepath)


if __name__ == "__main__":
    remove_comments_recursively()
