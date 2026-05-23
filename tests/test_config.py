"""Tests for configuration management."""

import json
import os
import pytest
from src.common.config import Config


class TestConfig:
    def test_load_valid_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"db": {"host": "localhost", "port": 5432}}))
        config = Config(str(config_file))
        assert config.get("db.host") == "localhost"
        assert config.get("db.port") == 5432

    def test_load_invalid_json_raises_valueerror(self, tmp_path):
        """Invalid JSON should raise ValueError with path context."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json}")
        with pytest.raises(ValueError, match="Failed to parse JSON config"):
            Config(str(config_file))

    def test_load_invalid_json_includes_line_col(self, tmp_path):
        """Error message should include line and column info."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{\n  "key": invalid\n}')
        with pytest.raises(ValueError, match=r"line \d+, column \d+"):
            Config(str(config_file))

    def test_load_missing_file_raises(self, tmp_path):
        """Missing config file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            Config(str(tmp_path / "nonexistent.json"))

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
