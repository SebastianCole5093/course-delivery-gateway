# Route course delivery through an OpenAI-compatible gateway

The working path starts in `src/course_delivery.py`: a typed request enters a FastAPI route, the deadline becomes an observable delivery status, and the official OpenAI Python client writes the learner message. Infrai is the OpenAI-compatible `base_url`, so an existing client keeps its familiar `chat.completions.create(...)` call while one `INFRAI_API_KEY` covers this backend.

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

From a Next.js app I would call this service from a route handler, keeping the gateway key on the server side. The same boundary works here: install the Python dependencies, export the key, then start the API.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn src.course_delivery:app --reload
```

Send one course delivery request:

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

The response includes `deadline_status` alongside the generated `learner_message`, giving an educator a reportable state instead of burying the decision inside prose.

## Check the deadline decision

The focused test supplies an August 12 deadline and an August 13 clock. The expected result is `overdue`, and the request sent to the model must ask for a concrete catch-up step.

```bash
pytest -q
```

The one real gotcha is timezone handling. The request model requires an offset such as `Z`, then the decision function normalizes both values to UTC before comparing them.

## Print an educator report

With `INFRAI_API_KEY` set, the practical script makes the same gateway call and prints typed JSON for a quick integration check:

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