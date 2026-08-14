from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.course_delivery import (
    CourseDeliveryRequest,
    DeadlineStatus,
    deliver_course,
)


class RecordingCompletions:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def create(self, *, model: str, messages: list[dict[str, str]]) -> SimpleNamespace:
        assert model == "auto"
        self.messages = messages
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Open the lesson and complete the checkout-state exercise."
                    )
                )
            ]
        )


def test_overdue_learner_enters_catch_up_delivery() -> None:
    completions = RecordingCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    request = CourseDeliveryRequest(
        course_title="Practical TypeScript",
        lesson_title="Model a checkout state",
        learner_name="Mina",
        deadline=datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc),
    )

    delivery = deliver_course(
        request,
        now=datetime(2026, 8, 13, 9, 0, tzinfo=timezone.utc),
        client=client,
    )

    assert delivery.deadline_status is DeadlineStatus.OVERDUE
    assert delivery.learner_message.startswith("Open the lesson")
    assert "concrete catch-up step" in completions.messages[0]["content"]


def test_course_deadline_requires_timezone() -> None:
    with pytest.raises(ValidationError, match="timezone offset"):
        CourseDeliveryRequest(
            course_title="Practical TypeScript",
            lesson_title="Model a checkout state",
            learner_name="Mina",
            deadline=datetime(2026, 8, 12, 9, 0),
        )
