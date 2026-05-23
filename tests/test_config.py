import pytest
from src.common.config import Config, _coerce_value


class TestConfig:
    def test_load_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text('{"app": {"name": "test", "port": 8080}}')
        config = Config(str(config_file))
        assert config.get("app.name") == "test"
        assert config.get("app.port") == 8080

    def test_default_value(self):
        config = Config()
        assert config.get("nonexistent.key", "default") == "default"

    def test_set_value(self):
        config = Config()
        config.set("database.host", "localhost")
        assert config.get("database.host") == "localhost"

    def test_nested_set(self):
        config = Config()
        config.set("a.b.c.d", "value")
        assert config.get("a.b.c.d") == "value"

    def test_to_dict(self):
        config = Config()
        config.set("key1", "value1")
        config.set("key2", "value2")
        data = config.to_dict()
        assert data["key1"] == "value1"
        assert data["key2"] == "value2"


class TestCoerceValue:
    def test_coerce_int(self):
        assert _coerce_value("8080") == 8080
        assert isinstance(_coerce_value("8080"), int)

    def test_coerce_float(self):
        assert _coerce_value("3.14") == 3.14
        assert isinstance(_coerce_value("3.14"), float)

    def test_coerce_bool_true(self):
        assert _coerce_value("true") is True
        assert _coerce_value("True") is True
        assert _coerce_value("TRUE") is True

    def test_coerce_bool_false(self):
        assert _coerce_value("false") is False
        assert _coerce_value("False") is False

    def test_coerce_string(self):
        assert _coerce_value("hello") == "hello"
        assert _coerce_value("localhost") == "localhost"


class TestEnvOverrideCoercion:
    """Regression test: AO_ env overrides should be coerced to proper types."""

    def test_env_int_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_PORT", "8080")
        config = Config()
        assert config.get("app.port") == 8080
        assert isinstance(config.get("app.port"), int)

    def test_env_float_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_TIMEOUT", "30.5")
        config = Config()
        assert config.get("app.timeout") == 30.5
        assert isinstance(config.get("app.timeout"), float)

    def test_env_bool_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_DEBUG", "true")
        config = Config()
        assert config.get("app.debug") is True

    def test_env_string_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_NAME", "myapp")
        config = Config()
        assert config.get("app.name") == "myapp"
        assert isinstance(config.get("app.name"), str)

    def test_env_override_does_not_clobber_file_config(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.json"
        config_file.write_text('{"app": {"name": "original", "port": 3000}}')
        monkeypatch.setenv("AO_APP_PORT", "8080")
        config = Config(str(config_file))
        assert config.get("app.port") == 8080
        assert config.get("app.name") == "original"
