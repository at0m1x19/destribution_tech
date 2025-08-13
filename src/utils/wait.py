import time
from typing import Any, Callable, Optional

import allure


def wait_until_condition_reached(
    condition_summary: str,
    condition: Callable[[], Any],
    timeout: int = 15,
    poll_interval: float = 1,
    expected_value: Optional[Any] = None,
) -> Any:
    """
    Polls `condition` until it becomes truthy (or equals `expected_value`) or times out.

    Parameters:
    - condition_summary: Human-readable description of what we are waiting for (shown as an Allure step).
    - condition: A zero-argument callable that returns the current value/state to check.
    - timeout: Maximum number of seconds to wait before failing with an AssertionError.
    - poll_interval: Number of seconds to sleep between polls.
    - expected_value: Optional target value to match against condition().
        • If provided, the wait succeeds as soon as condition() == expected_value.
        • If omitted (None), any truthy result from condition() is treated as success.

    Example:
        wait_until_condition_reached(
            condition_summary=f"Wait until fork {fork_id} appears in forks list",
            condition=lambda: any(
                item.get("id") == fork_id for item in api.list_gist_forks(gist_id).json()
            ),
            expected_value=True,
            timeout=15,
            poll_interval=2,
        )
    """
    with allure.step(condition_summary):
        until_time = time.time() + timeout
        last_result: Any = None
        while time.time() < until_time:
            last_result = condition()
            if expected_value is not None:
                if last_result == expected_value:
                    return last_result
            else:
                if last_result:
                    return last_result
            time.sleep(poll_interval)

        error_message = (
            f"Condition was not met within {timeout} seconds. Condition: {condition_summary}. "
            f"Last result: \"{last_result}\"."
        )
        if expected_value is not None:
            error_message = f"{error_message} Expected: \"{expected_value}\"."
        raise AssertionError(error_message)
