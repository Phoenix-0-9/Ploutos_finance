# Claude API Notes

## SDK

Use the official `anthropic` Python SDK:

```bash
pip install anthropic
```

```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4000,
    messages=[
        {"role": "user", "content": filled_prompt}
    ]
)

raw_text = response.content[0].text
```

## Getting clean JSON back

- Tell the model explicitly, in the prompt itself: "Respond with ONLY a
  valid JSON object. No markdown code fences, no preamble, no
  explanation outside the JSON."
- Still defensively strip code fences before `json.loads()`:
  ```python
  cleaned = raw_text.strip()
  if cleaned.startswith("```"):
      cleaned = cleaned.split("```")[1]
      if cleaned.startswith("json"):
          cleaned = cleaned[4:]
  parsed = json.loads(cleaned.strip())
  ```
- Validate `parsed` against the pydantic model from
  `docs/FORECAST_SCHEMA.md`. If it fails, retry once with the original
  prompt + this appended: "Your previous response was not valid JSON
  matching the required schema. Return ONLY the corrected JSON object."

## Model choice

- Default: `claude-sonnet-4-6` — good reasoning-to-cost ratio for a daily
  macro/FX summary task.
- If the user wants higher-quality reasoning (more nuanced scenario
  weighting), they can swap to `claude-opus-4-7` in `.env` /
  `config.py` — keep the model name as a config variable, not hardcoded.

## Cost control

- `max_tokens=4000` is generous for this output size; reduce if costs
  matter, the JSON schema above is not huge.
- Running once/day is cheap regardless — this is not a high-frequency
  use case.

## Error handling

- Network/API errors: retry with exponential backoff (2-3 attempts),
  then fail loudly (exit 1) — don't silently skip a day's forecast.
- Rate limit errors (429): respect `Retry-After` header if present.
