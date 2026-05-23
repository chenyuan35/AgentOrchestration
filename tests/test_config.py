import pytest
from src.common.config import Config, _coerce_value, _is_sensitive_key, _redact_dict, _REDACTED_PLACEHOLDER


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

    def test_coerce_bool_false(self):
        assert _coerce_value("false") is False

    def test_coerce_string(self):
        assert _coerce_value("hello") == "hello"


class TestEnvOverrideCoercion:
    def test_env_int_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_PORT", "8080")
        config = Config()
        assert config.get("app.port") == 8080
        assert isinstance(config.get("app.port"), int)

    def test_env_float_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_TIMEOUT", "30.5")
        config = Config()
        assert config.get("app.timeout") == 30.5

    def test_env_bool_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_DEBUG", "true")
        config = Config()
        assert config.get("app.debug") is True

    def test_env_string_override(self, monkeypatch):
        monkeypatch.setenv("AO_APP_NAME", "myapp")
        config = Config()
        assert config.get("app.name") == "myapp"


class TestIsSensitiveKey:
    def test_password_is_sensitive(self):
        assert _is_sensitive_key("database.password") is True

    def test_secret_is_sensitive(self):
        assert _is_sensitive_key("api.secret") is True

    def test_token_is_sensitive(self):
        assert _is_sensitive_key("auth.token") is True

    def test_api_key_is_sensitive(self):
        assert _is_sensitive_key("service.api_key") is True

    def test_access_token_is_sensitive(self):
        assert _is_sensitive_key("oauth.access_token") is True

    def test_name_is_not_sensitive(self):
        assert _is_sensitive_key("app.name") is False

    def test_port_is_not_sensitive(self):
        assert _is_sensitive_key("app.port") is False

    def test_host_is_not_sensitive(self):
        assert _is_sensitive_key("database.host") is False


class TestRedactDict:
    def test_redacts_password(self):
        data = {"database": {"host": "localhost", "password": "s3cret"}}
        result = _redact_dict(data)
        assert result["database"]["host"] == "localhost"
        assert result["database"]["password"] == _REDACTED_PLACEHOLDER

    def test_redacts_nested_secret(self):
        data = {"api": {"key": "abc123", "endpoint": "/v1"}}
        result = _redact_dict(data)
        assert result["api"]["key"] == _REDACTED_PLACEHOLDER
        assert result["api"]["endpoint"] == "/v1"

    def test_preserves_non_sensitive(self):
        data = {"app": {"name": "myapp", "port": 8080}}
        result = _redact_dict(data)
        assert result["app"]["name"] == "myapp"
        assert result["app"]["port"] == 8080

    def test_redacts_multiple_sensitive_keys(self):
        data = {
            "database": {"password": "secret1"},
            "api": {"token": "secret2"},
            "app": {"name": "myapp"}
        }
        result = _redact_dict(data)
        assert result["database"]["password"] == _REDACTED_PLACEHOLDER
        assert result["api"]["token"] == _REDACTED_PLACEHOLDER
        assert result["app"]["name"] == "myapp"


class TestToRedactedDict:
    """Regression test: to_redacted_dict should mask sensitive values."""

    def test_redacted_dict_masks_passwords(self):
        config = Config()
        config.set("database.password", "supersecret")
        config.set("database.host", "localhost")
        redacted = config.to_redacted_dict()
        assert redacted["database"]["password"] == _REDACTED_PLACEHOLDER
        assert redacted["database"]["host"] == "localhost"

    def test_redacted_dict_masks_tokens(self):
        config = Config()
        config.set("auth.access_token", "eyJhbGciOiJIUzI1NiJ9")
        config.set("auth.user_id", "user123")
        redacted = config.to_redacted_dict()
        assert redacted["auth"]["access_token"] == _REDACTED_PLACEHOLDER
        assert redacted["auth"]["user_id"] == "user123"

    def test_to_dict_still_returns_plain(self):
        config = Config()
        config.set("database.password", "supersecret")
        plain = config.to_dict()
        assert plain["database"]["password"] == "supersecret"

    def test_redacted_dict_does_not_modify_original(self):
        config = Config()
        config.set("api.key", "secret123")
        redacted = config.to_redacted_dict()
        assert redacted["api"]["key"] == _REDACTED_PLACEHOLDER
        assert config.get("api.key") == "secret123"
