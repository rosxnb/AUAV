from pathlib import Path


def does_path_exits(path: str) -> bool:
    path = Path(path)
    return path.exists()
