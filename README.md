## quizgen – Automated Quiz Generator with Opik observability

Generate multiple-choice questions from raw text using Groq models, with full tracing in Opik.

### Setup

- Create and activate a virtual env
  - macOS/Linux: `python -m venv .venv && source .venv/bin/activate`
  - Windows (PowerShell): `python -m venv .venv; .venv\\Scripts\\Activate.ps1`
- Install deps: `pip install -r requirements.txt`
- Configure environment:
  - Create `.env` and fill keys (see example below)
  - Or export `GROQ_API_KEY`, `OPIK_API_KEY`, and `OPIK_WORKSPACE`
  - Optionally: `opik configure`

### Run

```bash
python -m quizgen.app --input quizgen/data/sample.txt \
  --n 8 --out runs/quiz.jsonl \
  --model llama-3.1-8b-instant --temperature 0.2
```

Flags:
- `--input`: path to a `.txt` file
- `--n`: number of items to output
- `--out`: output JSONL path
- `--model`: Groq model, e.g., `llama-3.1-8b-instant`
- `--temperature`: sampling temperature
- `--feedback`: optional numeric score logged to Opik

### .env example

```
# Groq
GROQ_API_KEY=your_groq_key_here

# Opik (self-hosted)
OPIK_API_KEY=your_opik_api_key
OPIK_WORKSPACE=your_workspace
OPIK_BASE_URL=http://localhost:5173/api
```

### Output format (one JSON per line)

```json
{
  "source_id": "doc-001#chunk-3",
  "question": "…",
  "options": ["…","…","…","…"],
  "answer_index": 2,
  "explanation": "…",
  "meta": {"difficulty": 3, "judge_notes": "…", "time_sec": 75}
}
```

### Observability

- All LLM calls are traced via Opik (shimmed to no-op if Opik config is unavailable).
- Pipeline stages are decorated with `@track()`.
- Basic metrics and optional feedback score are recorded to the current trace. Open Opik to view traces for the run.

### Testing

```bash
pytest -q
```

The smoke test runs the CLI for `--n 2` and validates output. It skips automatically if `GROQ_API_KEY` is not set.

### Troubleshooting

- JSON parsing retries: The client extracts JSON even if the model wraps it in fences. If an error persists, lower temperature.
- Rate limits: Reduce `--n` and `--max-candidates-per-chunk`, or retry later.
- Self-hosted Opik: set `OPIK_BASE_URL` in `.env`.


