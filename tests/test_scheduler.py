import asyncio
import pytest
import time
from src.orchestrator.scheduler import TaskScheduler, PriorityQueue


class TestPriorityQueue:
    def test_push_pop(self):
        q = PriorityQueue()
        q.push("low", priority=0)
        q.push("high", priority=10)
        assert q.pop() == "high"
        assert q.pop() == "low"

    def test_peek(self):
        q = PriorityQueue()
        q.push("item", priority=0)
        assert q.peek() == "item"
        assert len(q) == 1

    def test_len(self):
        q = PriorityQueue()
        assert len(q) == 0
        q.push("a", priority=0)
        q.push("b", priority=1)
        assert len(q) == 2


class TestTaskScheduler:
    def test_enqueue(self):
        s = TaskScheduler()
        task_id = s.enqueue({"name": "test"}, queue="default", priority=5)
        assert task_id is not None
        assert len(s._queues["default"]) == 1

    def test_schedule(self):
        s = TaskScheduler()
        task_id = s.schedule({"name": "delayed"}, delay=10.0, queue="default")
        assert task_id is not None
        assert task_id in s._scheduled

    def test_schedule_uses_monotonic_time(self):
        """schedule() should use monotonic time, not wall clock time."""
        s = TaskScheduler()
        before = time.monotonic()
        task_id = s.schedule({"name": "delayed"}, delay=60.0)
        after = time.monotonic()
        scheduled_at = s._scheduled[task_id]
        # Scheduled time should be based on monotonic clock
        assert before + 60.0 <= scheduled_at <= after + 60.0

    def test_enqueue_uses_monotonic_time(self):
        """enqueue() should record monotonic time, not wall clock time."""
        s = TaskScheduler()
        before = time.monotonic()
        task_id = s.enqueue({"name": "test"})
        after = time.monotonic()
        task = None
        for item in s._queues["default"]._queue:
            if item[2]["id"] == task_id:
                task = item[2]
                break
        assert task is not None
        assert before <= task["enqueued_at"] <= after

    @pytest.mark.asyncio
    async def test_dequeue(self):
        s = TaskScheduler()
        s.enqueue({"name": "test"}, queue="default")
        task = await s.dequeue("default")
        assert task is not None
        assert task["name"] == "test"

    @pytest.mark.asyncio
    async def test_dequeue_empty(self):
        s = TaskScheduler()
        task = await s.dequeue("default")
        assert task is None

    def test_complete(self):
        s = TaskScheduler()
        task_id = s.enqueue({"name": "test"}, queue="default")
        s._in_flight[task_id] = {"id": task_id}
        assert s.complete(task_id) is True
        assert s.complete(task_id) is False

    def test_fail_retry(self):
        s = TaskScheduler()
        task_id = s.enqueue({"name": "test"}, queue="default")
        s._in_flight[task_id] = {"id": task_id, "retries": 0, "priority": 0}
        assert s.fail(task_id, "default") is True
        assert len(s._queues["default"]) == 1

    def test_fail_max_retries(self):
        s = TaskScheduler()
        task_id = s.enqueue({"name": "test"}, queue="default")
        s._in_flight[task_id] = {"id": task_id, "retries": 3, "priority": 0}
        assert s.fail(task_id, "default") is False
