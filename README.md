# SystemDoctor AI

> Your friendly AI system mechanic for Windows, macOS, Linux, hardware, and software issues.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/Status-Active-success)](#)
[![License](https://img.shields.io/badge/License-MIT-informational)](#license)
[![Hackathon](https://img.shields.io/badge/Built%20for-Hackathon-blueviolet)](#)

SystemDoctor AI is a multi-agent troubleshooting assistant that helps people understand computer problems, find likely root causes, and apply safer fixes step by step. It works across Windows, macOS, and Linux, and it can handle both hardware and software issues. It is designed to be easy for beginners and useful for advanced users.

## Why This Project Exists

Most people do not know where to start when a system breaks. Search results are noisy, advice is inconsistent, and random fixes can make things worse. SystemDoctor AI exists to turn that chaos into a guided path: ask smart questions, rank likely causes, suggest safer actions, and verify results.

## The Problem (In Very Simple Words)

When a laptop is slow or crashing, the real reason is often hidden.

- The same symptom can have many different causes.
- People try random fixes and lose time.
- Some fixes are risky and can create new problems.
- New users do not know what is safe to do first.

SystemDoctor AI acts like a calm helper that asks the right questions before suggesting fixes.

## What SystemDoctor AI Does

SystemDoctor AI is an AI-powered diagnostic assistant for system issues.

- It listens to your problem in plain language.
- It asks follow-up questions to collect evidence.
- It scores and ranks possible root causes.
- It gives practical, safer, step-by-step remediation guidance.
- It checks whether the fix worked and loops if needed.
- It can produce a final report of what happened.

This makes troubleshooting faster, clearer, and less scary in real life.

## Features

- Adaptive troubleshooting questions: Asks the next best question based on missing evidence.
- Hardware and software diagnosis: Covers both physical device issues and app/OS issues.
- Cross-platform support: Works with Windows, macOS, and Linux workflows.
- Confidence-based cause ranking: Shows likely causes with confidence levels.
- Step-by-step fix suggestions: Recommends structured actions in the right order.
- Safe troubleshooting guidance: Highlights risk levels and avoids dangerous shortcuts.
- Verification loop: Confirms if a fix worked, then adjusts if it did not.
- Optional online search support: Can enrich guidance using trusted online sources.
- Offline fallback mode: Still works with local logic when AI or internet is unavailable.
- Local-first behavior: Prioritizes resilient local execution for reliability and privacy.
- Report generation: Summarizes issue, evidence, diagnosis, and remediation outcomes.

## How It Works

1. User enters a problem description.
2. System asks follow-up questions.
3. AI and rules analyze the answers.
4. Possible causes are ranked.
5. Safe fix steps are suggested.
6. User applies steps and reports outcome.
7. System verifies and repeats if needed.
8. Final troubleshooting report is produced.

## Architecture Overview

SystemDoctor AI uses a modular multi-agent pipeline:

- Orchestrator: Coordinates the entire flow from intake to verification.
- Triage Agent: Quickly classifies issue type, context, and urgency.
- Question Engine: Chooses useful next questions to reduce uncertainty.
- Diagnosis Engine: Produces confidence-ranked probable causes.
- Remediation Engine: Generates actionable fix plans with safety context.
- Verification Engine: Checks outcomes and decides whether to retry or escalate.
- Specialist Agents: Domain experts for Windows, macOS, Linux, hardware, software, BIOS/boot, and driver/update scenarios.

## Tech Stack

| Area | Technologies |
|---|---|
| Language | Python 3.11+ |
| UI | Streamlit |
| API | FastAPI + Uvicorn |
| Data Models | Pydantic |
| Knowledge Layer | YAML decision trees, mappings, taxonomies, playbooks |
| AI Integration | Optional OpenAI and Gemini provider support |
| Config | python-dotenv + `.env` |
| Testing | Pytest (unit, integration, e2e) |
| Reliability | Local fallback logic + optional online enrichment |
| Collaboration | GitHub-based workflow |

## Project Structure

| Folder | What It Contains |
|---|---|
| `apps/` | Streamlit frontend and FastAPI backend entry points |
| `agents/` | Core orchestration agents and specialist troubleshooting agents |
| `knowledge/` | Playbooks, decision trees, mappings, and taxonomy files |
| `packages/` | Shared schemas and utility modules |
| `prompts/` | System/specialist/safety prompt templates |
| `tests/` | Unit, integration, and end-to-end tests |
| `infra/` | Docker and deployment-related infrastructure assets |
| `.foundry/` | Foundry scaffolding, templates, and evaluator workflow metadata |

## Quick Start (Beginner Friendly)

### 1) Clone the repository

```bash
git clone https://github.com/AbirChakraborty1703/System-Doctor-Agent.git
cd System-Doctor-Agent
```

### 2) Create a virtual environment

Windows (PowerShell):

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows (Command Prompt):

```bash
python -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Configure environment variables

Windows:

```bash
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

### 5) Start the app

```bash
streamlit run app.py
```

Open the local URL shown in the terminal (usually `http://localhost:8501`).

## Dependencies and Libraries

The project dependencies are managed in `requirements.txt`.

| Library | Why It Is Used |
|---|---|
| `streamlit` | Interactive web interface |
| `fastapi` | API endpoints for orchestration and session flow |
| `uvicorn` | ASGI server for running FastAPI |
| `pydantic` | Typed models and validation |
| `python-dotenv` | Loading config from `.env` |
| `PyYAML` | Reading knowledge files and decision trees |
| `pytest` | Automated testing |
| `openai` | Optional OpenAI model integration |
| `google-generativeai` | Optional Gemini model integration |

Install all required libraries with:

```bash
pip install -r requirements.txt
```

Optional AI provider libraries are already included, but you only need to provide keys if you want cloud AI enrichment.

## Run Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run Streamlit UI:

```bash
streamlit run app.py
```

Run FastAPI backend (optional):

```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Run test suite:

```bash
pytest -q
```

## Environment Variables

Use `.env.example` as your template.

### Core

- `LLM_PROVIDER`: `fallback`, `openai`, or `gemini`
- `MAX_QUESTIONS`: Maximum number of adaptive questions
- `MIN_CONFIDENCE_TO_STOP_QUESTIONS`: Stop threshold for diagnosis confidence
- `MAX_VERIFICATION_LOOPS`: Maximum verify-and-retry cycles

### Optional OpenAI

- `OPENAI_API_KEY`
- `OPENAI_MODEL`

### Optional Gemini

- `GEMINI_API_KEY`
- `GEMINI_MODEL`

### Optional Online Enrichment

- `ONLINE_SEARCH_ENABLED`
- `ONLINE_SEARCH_TIMEOUT_SECONDS`
- `ONLINE_SEARCH_MAX_RESULTS`
- `ONLINE_SEARCH_TRUSTED_DOMAINS`

### Optional API/CORS

- `ALLOWED_ORIGINS` (used by FastAPI CORS settings)

Important: The project can still run without API keys using local fallback mode.

## Common Problems and Fixes

### Dependencies fail to install

- Upgrade pip first: `pip install --upgrade pip`
- Ensure Python version is 3.11+
- Recreate virtual environment if needed

### Streamlit does not open

- Check whether port `8501` is already in use
- Run `streamlit run app.py --server.port 8502` to try another port
- Ensure virtual environment is activated

### Missing API keys

- Set `LLM_PROVIDER=fallback` in `.env`
- Leave provider keys empty if you want offline/local behavior

### Import errors

- Confirm you are running from repository root
- Reinstall dependencies: `pip install -r requirements.txt`
- Remove and recreate `.venv` if package state is broken

### App shows no useful diagnosis

- Provide clearer issue details and answer follow-up questions fully
- Increase `MAX_QUESTIONS` in `.env` for deeper evidence collection
- Verify knowledge files exist in `knowledge/`

### Unexpected behavior

- Run tests: `pytest -q`
- Check API health if backend is running: `http://localhost:8000/health`
- Review configuration in `.env`

## Safety and Reliability

SystemDoctor AI is built with a safety-first mindset.

- Avoids risky guidance whenever possible
- Uses confidence scores instead of pretending certainty
- Encourages cautious, reversible troubleshooting steps
- Supports verification loops before declaring success
- Can operate in offline fallback mode when external AI is unavailable

## Example Use Cases

### Slow laptop

SystemDoctor AI asks about startup load, storage, heat, and background apps, then suggests prioritized cleanup/tuning steps.

### Blue screen or random crash

It collects crash clues, recent updates, and hardware signals, then recommends safe checks and rollback-aware actions.

### No display

It guides through power, cable, GPU, and BIOS-level checks in safe order.

### Boot issue

It narrows whether startup failure is caused by OS, disk, update, or boot configuration.

### Wi-Fi problem

It checks adapter state, driver conditions, and network context to suggest targeted fixes.

### App not opening

It inspects compatibility, dependency, permissions, and runtime clues to identify likely root causes.

## Future Improvements

- Broader operating system and device knowledge coverage
- Smarter evidence fusion for higher diagnostic precision
- Enhanced UI polish and guided educational mode
- Richer, exportable troubleshooting reports
- Stronger evaluation and benchmark framework

## GitHub Readiness

- Secrets should remain outside version control (`.env` is excluded)
- `.gitignore` is configured for common sensitive/runtime files
- Repository is structured for safe public collaboration and hackathon visibility

## Contributing

Contributions are welcome. You can help by:

- Adding new troubleshooting playbooks
- Improving specialist agents
- Expanding tests and evaluation datasets
- Improving UX and beginner guidance

## License

MIT License.
