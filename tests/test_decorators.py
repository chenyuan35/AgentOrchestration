import pytest
from src.sdk.decorators import task, agent, on_event


class TestTaskDecorator:
    def test_task_config_on_wrapper(self):
        """__task_config__ should be accessible on the wrapper, not just the original function."""
        @task(name="my-task", retries=3, timeout=60)
        async def my_handler():
            pass

        assert hasattr(my_handler, "__task_config__")
        assert my_handler.__task_config__["name"] == "my-task"
        assert my_handler.__task_config__["retries"] == 3
        assert my_handler.__task_config__["timeout"] == 60

    def test_task_config_default_name(self):
        """Default task name should be the function name."""
        @task()
        async def my_handler():
            pass

        assert my_handler.__task_config__["name"] == "my_handler"

    def test_task_config_defaults(self):
        """Default retries and timeout should be 0 and 300."""
        @task(name="test")
        async def my_handler():
            pass

        assert my_handler.__task_config__["retries"] == 0
        assert my_handler.__task_config__["timeout"] == 300

    def test_task_preserves_function_name(self):
        """functools.wraps should preserve the original function name."""
        @task(name="custom")
        async def my_handler():
            pass

        assert my_handler.__name__ == "my_handler"


class TestAgentDecorator:
    def test_agent_config(self):
        @agent(name="test-agent", version="2.0.0", description="A test agent")
        class MyAgent:
            pass

        assert MyAgent.__agent_config__["name"] == "test-agent"
        assert MyAgent.__agent_config__["version"] == "2.0.0"
        assert MyAgent.__agent_config__["description"] == "A test agent"


class TestOnEventDecorator:
    def test_event_handler(self):
        @on_event("workflow.started")
        async def my_handler():
            pass

        assert hasattr(my_handler, "__event_handler__")
        assert my_handler.__event_handler__ == "workflow.started"
