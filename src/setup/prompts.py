from pathlib import Path


def prompt_create_path(path: Path, label: str) -> None:
    print(f"{label} '{path}' does not exist.")
    answer = input("Create it? [y/N]: ").strip().lower()

    if answer != "y":
        raise SystemExit("Aborted by user.")

    path.mkdir(parents=True, exist_ok=True)
