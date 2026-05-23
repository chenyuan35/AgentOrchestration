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

    def test_gauge_zero(self):
        self.metrics.gauge("connections.active", 0.0)
        snapshot = self.metrics.snapshot()
        assert snapshot["gauges"]["connections.active"] == 0.0

    def test_gauge_negative(self):
        self.metrics.gauge("temperature.delta", -5.5)
        snapshot = self.metrics.snapshot()
        assert snapshot["gauges"]["temperature.delta"] == -5.5

    def test_gauge_rejects_nan(self):
        with pytest.raises(ValueError, match="finite"):
            self.metrics.gauge("memory.usage", float("nan"))

    def test_gauge_rejects_inf(self):
        with pytest.raises(ValueError, match="finite"):
            self.metrics.gauge("memory.usage", float("inf"))

    def test_gauge_rejects_neg_inf(self):
        with pytest.raises(ValueError, match="finite"):
            self.metrics.gauge("memory.usage", float("-inf"))

    def test_gauge_does_not_store_on_reject(self):
        self.metrics.gauge("memory.usage", 50.0)
        with pytest.raises(ValueError):
            self.metrics.gauge("memory.usage", float("nan"))
        snapshot = self.metrics.snapshot()
        assert snapshot["gauges"]["memory.usage"] == 50.0

    def test_observe(self):
        self.metrics.observe("response.time", 0.5)
        self.metrics.observe("response.time", 1.5)
        snapshot = self.metrics.snapshot()
        assert snapshot["histograms"]["response.time"]["count"] == 2
        assert snapshot["histograms"]["response.time"]["avg"] == 1.0

    def test_timer(self):
        self.metrics.start_timer("operation")
        import time
        time.sleep(0.01)
        duration = self.metrics.stop_timer("operation")
        assert duration > 0.005
