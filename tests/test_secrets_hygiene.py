from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_covers_dotenv():
    text = (ROOT / ".gitignore").read_text()
    assert ".env" in text.splitlines()


def test_env_example_has_no_filled_secrets():
    text = (ROOT / ".env.example").read_text()
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if any(token in key for token in ("SECRET", "API_KEY", "CLIENT_ID", "CLIENT_SECRET", "TOKEN")):
            assert value == "", f"{key} must be empty in .env.example"


def test_repo_files_do_not_look_like_committed_secrets():
    forbidden = (".env",)
    for path in ROOT.rglob("*"):
        if path.is_dir() or "site-packages" in path.parts or ".venv" in path.parts:
            continue
        assert path.name not in forbidden
