# SystemDoctor AI

SystemDoctor AI is an AI-powered diagnostic assistant for hardware and software troubleshooting. It helps users and support teams identify root causes faster, apply safe remediation steps, and verify outcomes across Windows, macOS, and Linux.

## Problem Statement

Diagnosing system issues is often slow, fragmented, and error-prone.

- End users struggle to identify real root causes.
- Troubleshooting guidance is scattered across forums and vendor docs.
- Generic fixes often fail because they ignore system context.
- Support teams lose time in repetitive trial-and-error diagnosis.

SystemDoctor AI addresses this by combining structured questioning, evidence-based diagnosis, and safety-aware remediation in one guided workflow.

## Key Features

- Adaptive diagnostic questioning based on evidence gaps
- Hardware and software troubleshooting support
- Cross-platform workflows for Windows, macOS, and Linux
- Confidence-based root-cause ranking
- Safe, step-by-step remediation plans with risk labeling
- Verification loop to confirm if issues are resolved
- Optional online search enrichment when enabled
- Offline fallback behavior for local-only operation
- Local-first design for secure and resilient troubleshooting

## How It Works

1. User enters a system issue in natural language.
2. System asks targeted follow-up questions.
3. Diagnosis engine ranks probable causes with confidence.
4. Remediation engine suggests safe corrective actions.
5. Verification loop checks whether the fix worked.
6. Final report is generated for review and export.

## Architecture Overview

SystemDoctor AI uses a modular multi-agent pipeline:

- Orchestrator: Coordinates end-to-end diagnostic flow.
- Triage: Classifies issue type, severity, and operating context.
- Question Engine: Selects the next best question.
- Diagnosis Engine: Produces confidence-ranked root causes.
- Remediation Engine: Generates safe action plans.
- Verification Engine: Confirms outcomes and manages escalation.
- Specialist Agents: Domain-specific expertise by OS and issue class.

## Tech Stack

- Python
- Streamlit
- FastAPI
- Pydantic schemas and typed models
- Local knowledge files (YAML decision trees, taxonomies, playbooks)
- Optional LLM integration (OpenAI, Gemini)
- Offline deterministic fallback logic
- Pytest-based unit, integration, and end-to-end tests

## Project Structure

- apps/: Entry points for Streamlit UI and API services.
- agents/: Core orchestration, diagnostic, remediation, and specialist agents.
- knowledge/: Decision trees, mappings, taxonomies, and troubleshooting playbooks.
- packages/: Shared schemas and utility modules.
- prompts/: System, specialist, and safety prompt templates.
- tests/: Unit, integration, and e2e test suites.
- infra/: Container and deployment assets.
- .foundry/: Foundry metadata, templates, evaluators, and workflow scaffolding.

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/AbirChakraborty1703/System-Doctor-Agent.git
cd System-Doctor
```

### 2. Create a virtual environment

Windows (PowerShell):

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Windows:

```bash
copy .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

### 5. Run locally

```bash
streamlit run app.py
```

## Configuration

- Use .env.example as the baseline configuration template.
- Add only the variables required for your selected provider/workflow.
- The project can run without API keys using fallback/local logic.
- Optional online or AI enrichment can be enabled by setting provider-specific variables in .env.

Typical provider settings:

- LLM_PROVIDER=openai with OPENAI_API_KEY
- LLM_PROVIDER=gemini with GEMINI_API_KEY
- LLM_PROVIDER=fallback for offline deterministic mode

## Run Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Start Streamlit:

```bash
streamlit run app.py
```

Run tests:

```bash
pytest -q
```

Optional API server:

```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Development Notes

- Local-first behavior is supported to reduce external dependencies.
- Safety-first troubleshooting avoids destructive actions by default.
- Diagnosis is confidence-based and evidence-driven.
- The codebase is modular and designed for incremental extension.
- Specialist agents can be expanded for deeper platform coverage.

## GitHub Publication Readiness

- Sensitive files are excluded through .gitignore.
- Secrets, local tokens, and runtime artifacts should never be committed.
- Generated caches, logs, traces, and temporary outputs are excluded.
- Repository structure is prepared for safe public publishing.

Recommended publish commands:

```bash
git remote add origin https://github.com/AbirChakraborty1703/System-Doctor-Agent.git
git add .
git commit -m "Add production-ready README and gitignore"
git push -u origin main
```

## Future Improvements

- Expand troubleshooting knowledge coverage across more device classes.
- Add deeper OS-specific diagnostics and remediation intelligence.
- Improve verification loop reasoning and recovery guidance.
- Introduce richer report export formats and analytics.
- Enhance UI observability and runtime telemetry.
