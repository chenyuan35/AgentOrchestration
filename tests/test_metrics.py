import math
import pytest
from src.common.metrics import MetricsCollector


class TestMetricsCollector:
    def setup_method(self):
        self.metrics = MetricsCollector()

    def test_increment(self):
        self.metrics.increment("requests.total")
        self.metrics.increment("requests.total")
        snapshot = self.metrics.snapshot()
        assert snapshot["counters"]["requests.total"] == 2

    def test_gauge(self):
        self.metrics.gauge("memory.usage", 85.5)
        snapshot = self.metrics.snapshot()
        assert snapshot["gauges"]["memory.usage"] == 85.5

    def test_gauge_rejects_nan(self):
        with pytest.raises(ValueError, match="finite"):
            self.metrics.gauge("memory.usage", float("nan"))

    def test_gauge_rejects_inf(self):
        with pytest.raises(ValueError, match="finite"):
            self.metrics.gauge("memory.usage", float("inf"))

    def test_histogram_includes_min_max(self):
        self.metrics.observe("response.time", 0.5)
        self.metrics.observe("response.time", 1.5)
        self.metrics.observe("response.time", 0.2)
        snapshot = self.metrics.snapshot()
        hist = snapshot["histograms"]["response.time"]
        assert hist["count"] == 3
        assert hist["min"] == 0.2
        assert hist["max"] == 1.5
        assert hist["avg"] == pytest.approx(0.733, rel=0.01)

    def test_histogram_min_max_single_value(self):
        self.metrics.observe("response.time", 1.0)
        snapshot = self.metrics.snapshot()
        hist = snapshot["histograms"]["response.time"]
        assert hist["min"] == 1.0
        assert hist["max"] == 1.0

    def test_histogram_min_max_empty(self):
        snapshot = self.metrics.snapshot()
        assert "response.time" not in snapshot["histograms"]

    def test_observe(self):
        self.metrics.observe("response.time", 0.5)
        self.metrics.observe("response.time", 1.5)
        snapshot = self.metrics.snapshot()
        assert snapshot["histograms"]["response.time"]["count"] == 2

    def test_timer(self):
        self.metrics.start_timer("operation")
        import time
        time.sleep(0.01)
        duration = self.metrics.stop_timer("operation")
        assert duration > 0.005
