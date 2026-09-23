import os

from goblin import credentials


def test_api_key_validation_rejects_whitespace_and_short_values():
    assert credentials.is_valid_openai_api_key("sk-12345678901234567890")
    assert not credentials.is_valid_openai_api_key("sk-short")
    assert not credentials.is_valid_openai_api_key("sk-1234567890 1234567890")


def test_save_and_load_api_key_uses_restrictive_permissions(tmp_path, monkeypatch):
    key_path = tmp_path / "config" / "openai_api_key"
    monkeypatch.setattr(credentials, "_OPENAI_API_KEY_PATH", key_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    credentials.save_openai_api_key("sk-12345678901234567890")

    assert key_path.read_text(encoding="utf-8") == "sk-12345678901234567890\n"
    assert key_path.stat().st_mode & 0o777 == 0o600
    assert credentials.load_saved_openai_api_key() == "sk-12345678901234567890"


def test_delete_api_key_removes_file_and_environment(tmp_path, monkeypatch):
    key_path = tmp_path / "openai_api_key"
    key_path.write_text("sk-12345678901234567890\n", encoding="utf-8")
    monkeypatch.setattr(credentials, "_OPENAI_API_KEY_PATH", key_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-12345678901234567890")

    credentials.delete_openai_api_key()

    assert not key_path.exists()
    assert "OPENAI_API_KEY" not in os.environ
