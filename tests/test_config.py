"""Tests for configuration management."""

import os
import json
import pytest
from src.common.config import Config


class TestConfig:
    def test_load_valid_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"db": {"host": "localhost"}}))
        config = Config(str(config_file))
        assert config.get("db.host") == "localhost"

    def test_env_override_simple(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))
        os.environ["AO_DB_HOST"] = "remote"
        try:
            config = Config(str(config_file))
            assert config.get("db.host") == "remote"
        finally:
            del os.environ["AO_DB_HOST"]

    def test_env_override_double_underscore_literal(self, tmp_path):
        """Double underscore should map to literal underscore in key."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))
        os.environ["AO_MY__KEY"] = "value"
        try:
            config = Config(str(config_file))
            assert config.get("my_key") == "value"
        finally:
            del os.environ["AO_MY__KEY"]

    def test_env_override_single_underscore_nested(self, tmp_path):
        """Single underscore should map to dot (nested key)."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))
        os.environ["AO_DB_HOST"] = "localhost"
        try:
            config = Config(str(config_file))
            assert config.get("db.host") == "localhost"
        finally:
            del os.environ["AO_DB_HOST"]

    def test_env_override_mixed_underscores(self, tmp_path):
        """Mix of single and double underscores."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))
        os.environ["AO_LOG__FILE_PATH"] = "/var/log/app.log"
        try:
            config = Config(str(config_file))
            assert config.get("log_file.path") == "/var/log/app.log"
        finally:
            del os.environ["AO_LOG__FILE_PATH"]

    def test_get_nested(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"a": {"b": {"c": "deep"}}}))
        config = Config(str(config_file))
        assert config.get("a.b.c") == "deep"

    def test_get_default(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))
        config = Config(str(config_file))
        assert config.get("missing", "default") == "default"
