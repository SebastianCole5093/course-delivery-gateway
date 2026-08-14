"""Run a course delivery and print the educator-facing result."""

from datetime import datetime, timezone

from course_delivery import CourseDeliveryRequest, deliver_course, gateway_client


def main() -> None:
    request = CourseDeliveryRequest(
        course_title="Practical TypeScript",
        lesson_title="Model a checkout state",
        learner_name="Mina",
        deadline=datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc),
    )
    delivery = deliver_course(
        request,
        now=datetime.now(timezone.utc),
        client=gateway_client(),
    )
    print(delivery.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
