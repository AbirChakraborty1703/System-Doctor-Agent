# SystemDoctor AI

SystemDoctor AI is a production-style multi-agent troubleshooting assistant for hardware and software incidents across Windows, macOS, and Linux. It combines deterministic triage, adaptive questioning, evidence-backed diagnosis, safe remediation planning, and verification into a single Streamlit-based diagnostic console.

## Features

- Free-text symptom intake
- Adaptive follow-up questioning
- Issue triage (category, severity, OS)
- Top-3 diagnosis ranking with confidence and evidence
- Safe remediation planning with risk guardrails
- Verification loop and escalation guidance
- Session report export
- Streamlit diagnostic cockpit UI
- FastAPI runtime endpoints for integration
- Deterministic fallback when API keys are missing

## Tech Stack

- Python 3.11+
- Streamlit
- FastAPI
- Pydantic
- SQLite
- PyYAML
- OpenAI / Gemini providers with deterministic fallback
- Pytest

## Repository layout

- apps/streamlit: Primary interactive diagnostic cockpit
- apps/api: FastAPI endpoints for orchestration access
- agents: Multi-agent implementation (orchestrator, triage, questioning, diagnosis, remediation, verification, specialists)
- knowledge: Decision trees, playbooks, command catalog, mappings, taxonomies
- packages/schemas: Typed contracts
- packages/shared_utils: Config, storage, loader, safety, reporting, provider abstractions
- tests: Unit, integration, and e2e tests
- infra/docker: Container assets
- .foundry: Foundry-ready metadata, evaluators, benchmarks, and experiment assets

## Architecture Overview

The project is organized as a layered workflow:

- Intake and triage classify the issue and infer the operating system.
- The question engine asks the next best question based on evidence gaps.
- The diagnosis engine ranks the top three causes with confidence and supporting evidence.
- The remediation engine generates safe, risk-labeled fix steps with rollback guidance.
- The verification loop checks whether the fix worked and either closes, refines, or escalates the case.
- The Streamlit dashboard presents the workflow in a polished enterprise-style console.

## Quickstart (local)

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template:

```bash
copy .env.example .env
```

4. Run Streamlit app:

```bash
streamlit run app.py
```

5. Optional API runtime:

```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Running tests

```bash
pytest -q
```

## LLM provider strategy

- Set `LLM_PROVIDER=openai` and `OPENAI_API_KEY` for OpenAI.
- Set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` for Gemini.
- Keep `LLM_PROVIDER=fallback` to run fully local deterministic logic.

## Hackathon Context

SystemDoctor AI is designed for a TCS-level innovation showcase: it demonstrates applied AI, deterministic decision support, safe automation, and a professional dashboard experience suitable for technical evaluation and live demos.

## Screenshots

Add product screenshots here before publishing if desired.

## Future Improvements

- Add richer hardware telemetry ingestion.
- Expand the knowledge base with more device-specific playbooks.
- Add saved session export formats beyond Markdown.
- Add authentication and multi-user session history for team deployments.

## Safety model

- Every remediation step receives a risk level.
- Medium/high/critical steps require explicit confirmation.
- Critical destructive actions are blocked by default.
- Firmware/bootloader/disk operations trigger additional warning behavior.

## Hackathon demo flow

1. Enter free-text issue.
2. Answer adaptive questions.
3. Review top diagnoses and confidence bars.
4. Apply safe remediation guidance.
5. Verify outcome and loop if unresolved.
6. Export final report.

## Deployment readiness

- Docker assets available in `infra/docker`.
- API supports external integrations.
- .foundry assets support future experiment/evaluation automation.
- Structured logs and persisted sessions support operational tracking.
- The repository is configured to be publication-safe and ignores local secrets, caches, logs, and generated database files.
