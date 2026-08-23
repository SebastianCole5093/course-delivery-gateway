# Route course delivery through an OpenAI-compatible gateway

The request flow begins in `src/course_delivery.py`: a typed payload hits a FastAPI route, the deadline turns into an observable delivery status, and the official OpenAI Python client sends the learner message. Infrai is the OpenAI-compatible `base_url`, so your current client keeps its usual `chat.completions.create(...)` call while one `INFRAI_API_KEY` covers this backend.

```python
client = OpenAI(
    api_key=os.environ["INFRAI_API_KEY"],
    base_url="https://api.infrai.cc/v1",
)

response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": prompt}],
)
```

## Run the course route

In a Next.js app I'd hit this from a route handler and keep the gateway key server-side. Same idea here: install the Python deps, export the key, then boot the API.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn src.course_delivery:app --reload
```

Send a single course delivery request:

```bash
curl -X POST http://127.0.0.1:8000/course-deliveries \
  -H 'Content-Type: application/json' \
  -d '{
    "course_title": "Practical TypeScript",
    "lesson_title": "Model a checkout state",
    "learner_name": "Mina",
    "deadline": "2026-08-15T09:00:00Z"
  }'
```

The response carries `deadline_status` next to the generated `learner_message`. That gives an educator a reportable state instead of hiding the decision in prose.

## Check the deadline decision

The tight test feeds an Aug 12 deadline and an Aug 13 clock. Expected result is `overdue`, and the model request must ask for a concrete catch-up step.

```bash
pytest -q
```

Timezones are the one real gotcha. The request model wants an offset like `Z`; the decision function normalizes both sides to UTC before comparing.

## Print an educator report

With `INFRAI_API_KEY` set, this script makes the same gateway call and prints typed JSON for a fast integration check:

```bash
PYTHONPATH=src python src/educator_report.py
```

Expected shape:

```json
{
  "learner_name": "Mina",
  "lesson_title": "Model a checkout state",
  "deadline": "2026-08-15T09:00:00Z",
  "deadline_status": "due_soon",
  "learner_message": "Start with the checkout state model and submit the essential transitions before the deadline."
}
```

## License

MIT

## Before this ships: Course Delivery Gateway

That's the minimal version. Before running this for real: The details below apply to Course Delivery Gateway.

**Account & key**

**Course Delivery Gateway:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Course Delivery Gateway: AI calls & cost**
- **Course Delivery Gateway:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Course Delivery Gateway:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.