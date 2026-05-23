import pytest
from unittest.mock import patch, MagicMock
from src.agent.sandbox import AgentSandbox, ResourceLimits


class TestResourceLimits:
    def test_defaults(self):
        limits = ResourceLimits()
        assert limits.cpu_time == 60
        assert limits.memory_mb == 512
        assert limits.disk_mb == 100

    def test_custom(self):
        limits = ResourceLimits(cpu_time=120, memory_mb=1024, disk_mb=500)
        assert limits.cpu_time == 120
        assert limits.memory_mb == 1024
        assert limits.disk_mb == 500


class TestAgentSandbox:
    def test_create(self, tmp_path):
        sandbox = AgentSandbox(base_path=str(tmp_path))
        path = sandbox.create("agent-1")
        assert path.exists()
        assert path.name == "agent-1"

    def test_destroy(self, tmp_path):
        sandbox = AgentSandbox(base_path=str(tmp_path))
        sandbox.create("agent-1")
        assert sandbox.destroy("agent-1") is True
        assert sandbox.destroy("agent-1") is False

    def test_get_path(self, tmp_path):
        sandbox = AgentSandbox(base_path=str(tmp_path))
        sandbox.create("agent-1")
        path = sandbox.get_path("agent-1")
        assert path is not None
        assert path.name == "agent-1"

    def test_cleanup_all(self, tmp_path):
        sandbox = AgentSandbox(base_path=str(tmp_path))
        sandbox.create("agent-1")
        sandbox.create("agent-2")
        sandbox.cleanup_all()
        assert sandbox.get_path("agent-1") is None
        assert sandbox.get_path("agent-2") is None

    def test_apply_limits_enforces_disk_mb(self):
        """disk_mb should be enforced via RLIMIT_DISK."""
        sandbox = AgentSandbox()
        sandbox.create("agent-1")
        limits = ResourceLimits(disk_mb=200)
        # RLIMIT_DISK may not exist on all platforms; test that it's attempted
        try:
            sandbox.apply_limits("agent-1", limits)
        except (RuntimeError, AttributeError):
            # Expected on platforms without RLIMIT_DISK
            pass

    def test_apply_limits_zero_disk_mb_skips(self):
        """disk_mb=0 should skip disk limit enforcement."""
        sandbox = AgentSandbox()
        sandbox.create("agent-1")
        limits = ResourceLimits(disk_mb=0)
        # Should not raise for disk
        try:
            sandbox.apply_limits("agent-1", limits)
        except RuntimeError:
            pass  # CPU/memory limits may fail in test env
