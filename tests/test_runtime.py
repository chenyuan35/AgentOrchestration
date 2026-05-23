import subprocess
import pytest
from unittest.mock import MagicMock, patch
from src.agent.runtime import AgentRuntime, RuntimeState


class TestAgentRuntime:
    def setup_method(self):
        self.runtime = AgentRuntime()

    def test_start(self):
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc
            result = self.runtime.start("agent-1", ["echo", "hello"])
            assert result is True
            assert self.runtime.get_state("agent-1") == RuntimeState.RUNNING

    def test_start_already_running(self):
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc
            self.runtime.start("agent-1", ["echo", "hello"])
            result = self.runtime.start("agent-1", ["echo", "hello"])
            assert result is False

    def test_start_failure(self):
        with patch("subprocess.Popen", side_effect=Exception("fail")):
            result = self.runtime.start("agent-1", ["echo", "hello"])
            assert result is False
            assert self.runtime.get_state("agent-1") == RuntimeState.CRASHED

    def test_stop_success(self):
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            self.runtime.start("agent-1", ["echo", "hello"])
            result = self.runtime.stop("agent-1", timeout=5)
            assert result is True
            mock_proc.send_signal.assert_called_once_with(subprocess.signal.SIGTERM)

    def test_stop_already_stopped(self):
        result = self.runtime.stop("nonexistent", timeout=5)
        assert result is False

    def test_stop_timeout_kills(self):
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
            mock_popen.return_value = mock_proc
            self.runtime.start("agent-1", ["echo", "hello"])
            result = self.runtime.stop("agent-1", timeout=5)
            assert result is True
            mock_proc.kill.assert_called_once()

    def test_stop_negative_timeout_raises(self):
        """Negative timeout should raise ValueError before any signal is sent."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            self.runtime.stop("agent-1", timeout=-1)

    def test_stop_zero_timeout_raises(self):
        """Zero timeout should raise ValueError before any signal is sent."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            self.runtime.stop("agent-1", timeout=0)

    def test_stop_validation_happens_before_signal(self):
        """ValueError should be raised even if agent doesn't exist."""
        with pytest.raises(ValueError):
            self.runtime.stop("nonexistent", timeout=-5)

    def test_get_state_crashed(self):
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = 1  # Process exited
            mock_popen.return_value = mock_proc
            self.runtime.start("agent-1", ["echo", "hello"])
            state = self.runtime.get_state("agent-1")
            assert state == RuntimeState.CRASHED

    def test_is_running(self):
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc
            self.runtime.start("agent-1", ["echo", "hello"])
            assert self.runtime.is_running("agent-1") is True
