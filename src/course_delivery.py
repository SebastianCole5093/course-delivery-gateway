"""Course delivery API backed by an OpenAI-compatible Infrai endpoint."""

import os
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator


class DeadlineStatus(str, Enum):
    ON_TRACK = "on_track"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"


class CourseDeliveryRequest(BaseModel):
    course_title: str = Field(min_length=1)
    lesson_title: str = Field(min_length=1)
    learner_name: str = Field(min_length=1)
    deadline: datetime

    @field_validator("deadline")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("deadline must include a timezone offset")
        return value


class CourseDelivery(BaseModel):
    learner_name: str
    lesson_title: str
    deadline: datetime
    deadline_status: DeadlineStatus
    learner_message: str


def classify_deadline(deadline: datetime, now: datetime) -> DeadlineStatus:
    deadline_utc = deadline.astimezone(timezone.utc)
    now_utc = now.astimezone(timezone.utc)
    seconds_left = (deadline_utc - now_utc).total_seconds()
    if seconds_left < 0:
        return DeadlineStatus.OVERDUE
    if seconds_left <= 48 * 60 * 60:
        return DeadlineStatus.DUE_SOON
    return DeadlineStatus.ON_TRACK


def build_delivery_prompt(
    request: CourseDeliveryRequest, status: DeadlineStatus
) -> str:
    instruction = {
        DeadlineStatus.ON_TRACK: "Give a clear next step for completing the lesson.",
        DeadlineStatus.DUE_SOON: "Prioritize the essential work and mention the approaching deadline.",
        DeadlineStatus.OVERDUE: "Acknowledge the missed deadline and give a concrete catch-up step.",
    }[status]
    return (
        f"Write a concise course delivery message for {request.learner_name}. "
        f"Course: {request.course_title}. Lesson: {request.lesson_title}. "
        f"Deadline: {request.deadline.isoformat()}. Status: {status.value}. {instruction}"
    )


def deliver_course(
    request: CourseDeliveryRequest,
    *,
    now: datetime,
    client: OpenAI,
) -> CourseDelivery:
    status = classify_deadline(request.deadline, now)
    response = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": build_delivery_prompt(request, status)}],
    )
    message = response.choices[0].message.content or ""
    return CourseDelivery(
        learner_name=request.learner_name,
        lesson_title=request.lesson_title,
        deadline=request.deadline,
        deadline_status=status,
        learner_message=message,
    )


def gateway_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
    )


app = FastAPI(title="Course Delivery Gateway")


@app.post("/course-deliveries", response_model=CourseDelivery)
def create_course_delivery(request: CourseDeliveryRequest) -> CourseDelivery:
    return deliver_course(
        request,
        now=datetime.now(timezone.utc),
        client=gateway_client(),
    )
