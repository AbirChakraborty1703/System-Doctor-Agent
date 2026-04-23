# SystemDoctor AI
Production-Ready Multi-Agent Blueprint for Cross-OS Hardware and Software Diagnosis

## 1. System Overview

### Vision
SystemDoctor AI is an AI diagnostic copilot that helps users identify and resolve computer issues across Windows, macOS, and Linux through adaptive questioning, evidence-based diagnosis, and safe remediation guidance.

### Problem Statement
Most users report symptoms, not root causes. Traditional support is slow, OS-fragmented, and inconsistent. SystemDoctor AI standardizes diagnosis by:

1. Understanding free-text problem reports.
2. Collecting missing evidence via targeted follow-up questions.
3. Ranking likely root causes with confidence.
4. Producing safe, actionable fix steps.
5. Verifying outcomes and escalating when needed.

### Key Capabilities

1. Free-text symptom intake.
2. Adaptive questioning based on uncertainty.
3. Hardware and software troubleshooting in one flow.
4. Cross-platform support for Windows, macOS, Linux.
5. BIOS and boot issue handling.
6. Update and driver issue handling.
7. Top-k diagnosis ranking with confidence scores.
8. Safe remediation playbooks with risk labels.
9. Verification loop after each remediation attempt.
10. Escalation guidance for unresolved or risky scenarios.
11. Session report export for support handoff.
12. Telemetry and evaluation for continuous improvement.

---

## 2. High-Level Architecture

### Architecture Diagram

```text
+-----------------------+        +----------------------+
| Web UI / Streamlit UI | -----> | FastAPI Gateway/API  |
+-----------------------+        +----------------------+
                                           |
                                           v
                                  +------------------+
                                  | Orchestrator     |
                                  | Agent            |
                                  +------------------+
                                     |   |   |   |
                                     |   |   |   +------------------------------+
                                     |   |   +-------------------+              |
                                     |   +-----------+           |              |
                                     v               v           v              v
                              +-----------+   +-----------+   +-----------+  +-----------+
                              | Triage    |   | Question  |   | Diagnosis |  | Remediation|
                              | Agent     |   | Engine    |   | Engine    |  | Agent      |
                              +-----------+   +-----------+   +-----------+  +-----------+
                                     |              |               |              |
                                     +--------------+---------------+--------------+
                                                    |
                                                    v
                                           +------------------+
                                           | Verification     |
                                           | Agent            |
                                           +------------------+
                                                    |
                                                    v
                                           +------------------+
                                           | Final Report     |
                                           +------------------+

All agents read:
- Knowledge Layer (decision trees, playbooks, command catalog, hardware matrix)
- Vector Retrieval (FAISS or Chroma)

All stages write:
- Trace Logs, Metrics, Feedback, Evaluation Artifacts
```

### Data Flow

1. UI sends user issue description to FastAPI.
2. API creates a session and forwards context to Orchestrator.
3. Orchestrator calls Triage to detect domain and urgency.
4. Question Engine asks the highest-value next question.
5. Specialist agents provide domain evidence.
6. Diagnosis Engine aggregates evidence and ranks root causes.
7. Remediation Agent generates safe step-by-step fixes.
8. Verification Agent confirms result and loops if unresolved.
9. API returns report with confidence, actions, and escalation guidance.

### Agent Interaction Flow

1. Orchestrator sets workflow state and confidence threshold.
2. Triage labels category and severity.
3. Question Engine drives evidence collection until stop condition.
4. Specialist agents enrich context.
5. Diagnosis Engine computes ranked hypotheses.
6. Remediation Agent maps hypotheses to fix sequences.
7. Verification Agent validates outcome and decides close or continue.

---

## 3. Detailed Agent Design

### 3.1 Orchestrator Agent

- Responsibility: Own global state, route tasks to agents, enforce workflow policy.
- Inputs: Session state, user profile, latest evidence, confidence threshold.
- Outputs: Next agent call, state transitions, final workflow status.
- Tools used: Workflow state store, policy checker, telemetry logger.
- Prompt strategy: Deterministic controller prompt with strict JSON action schema.
- Example behavior: If confidence is below threshold after 5 questions, invoke specialist plus one final diagnostic pass.

### 3.2 Triage Agent

- Responsibility: Initial classification of issue domain and urgency.
- Inputs: Free-text complaint, OS, hardware context.
- Outputs: Primary category, secondary category, severity, missing critical data list.
- Tools used: Lightweight classifier model, taxonomy lookup, symptom normalizer.
- Prompt strategy: Short classification prompt with fixed label set and confidence output.
- Example behavior: Detects "boot loop after update" as BIOS/Boot plus Update/Driver, severity high.

### 3.3 Question Engine Agent

- Responsibility: Generate adaptive next-best questions to reduce uncertainty.
- Inputs: Current hypotheses, missing evidence, previous answers.
- Outputs: Ranked question list, rationale, expected information gain.
- Tools used: Information gain scorer, dialogue memory, question template library.
- Prompt strategy: Ask one high-yield question at a time and avoid repeated questions.
- Example behavior: Asks "Do you see manufacturer logo before restart?" to separate BIOS vs OS fault.

### 3.4 Diagnosis Engine Agent

- Responsibility: Produce ranked root-cause hypotheses with confidence and evidence.
- Inputs: Full session evidence, specialist outputs, retrieved knowledge.
- Outputs: Top-3 diagnoses, confidence scores, supporting and conflicting evidence.
- Tools used: Rule engine, retrieval augmented context, confidence calibration module.
- Prompt strategy: Evidence-first reasoning with explicit uncertainty and contradiction handling.
- Example behavior: Returns "Corrupt GPU driver (0.62), failing SSD (0.21), OS patch regression (0.17)".

### 3.5 Remediation Agent

- Responsibility: Convert diagnosis into safe, ordered fix plan by OS.
- Inputs: Ranked diagnosis, OS context, user skill level, risk policy.
- Outputs: Step-by-step remediation, risk label, rollback advice, expected outcome.
- Tools used: Playbook mapper, command catalog, safety policy engine.
- Prompt strategy: Action plan format with prerequisites, commands, checkpoints.
- Example behavior: Suggests safe mode driver rollback before firmware updates.

### 3.6 Verification Agent

- Responsibility: Confirm whether issue is resolved and decide loop or closure.
- Inputs: User feedback, post-fix symptoms, telemetry checkpoints.
- Outputs: Resolved status, residual risk, next-step recommendation.
- Tools used: Outcome checklist, symptom comparator, escalation rules.
- Prompt strategy: Binary validation plus residual symptom probing.
- Example behavior: If audio fixed but random freezes remain, loop back with narrowed hypotheses.

### 3.7 Hardware Specialist Agent

- Responsibility: Hardware-centric interpretation of symptoms.
- Inputs: Device age, noise/heat/power symptoms, storage indicators.
- Outputs: Hardware failure probabilities and tests.
- Tools used: Hardware fault matrix, sensor interpretation rules.
- Prompt strategy: Distinguish intermittent vs hard failures using observable signals.
- Example behavior: Flags potential PSU instability from reboot-under-load pattern.

### 3.8 Software Specialist Agent

- Responsibility: Software stack diagnosis across apps, services, dependencies.
- Inputs: Error messages, recent installs, app crash patterns.
- Outputs: Software fault hypotheses and fix suggestions.
- Tools used: App error signature map, dependency conflict rules.
- Prompt strategy: Correlate version changes with symptom onset timeline.
- Example behavior: Detects library mismatch after partial app upgrade.

### 3.9 Windows Specialist Agent

- Responsibility: Windows-specific diagnostics and fix workflows.
- Inputs: Windows version, update history, event log signals.
- Outputs: Windows-targeted root causes and commands.
- Tools used: Windows command catalog, registry-safe operations, update playbooks.
- Prompt strategy: Prefer non-destructive steps first, then advanced repair paths.
- Example behavior: Suggests DISM then SFC sequence before in-place repair.

### 3.10 macOS Specialist Agent

- Responsibility: macOS-specific diagnostics and recovery guidance.
- Inputs: macOS version, startup behavior, panic patterns.
- Outputs: macOS-targeted hypotheses and remediation steps.
- Tools used: macOS command catalog, safe boot and recovery playbooks.
- Prompt strategy: Prioritize data-safe checks and system integrity constraints.
- Example behavior: Uses Safe Mode isolation to separate extension issue from hardware issue.

### 3.11 Linux Specialist Agent

- Responsibility: Linux distro-aware diagnostics and remediation.
- Inputs: Distro, kernel version, service logs, package manager state.
- Outputs: Linux-specific root causes and command steps.
- Tools used: Linux command catalog by distro, systemd and log rule sets.
- Prompt strategy: Ask distro-specific clarifiers before giving commands.
- Example behavior: Suggests journalctl evidence collection then package rollback.

### 3.12 BIOS/Boot Specialist Agent

- Responsibility: Diagnose firmware, POST, bootloader, and startup chain faults.
- Inputs: Beep codes, boot sequence behavior, firmware changes.
- Outputs: Boot chain diagnosis and firmware-safe action plan.
- Tools used: BIOS symptom tree, bootloader troubleshooting playbooks.
- Prompt strategy: Strict safety mode and clear warnings before firmware actions.
- Example behavior: Recommends resetting boot order and checking UEFI mode consistency.

### 3.13 Update/Driver Specialist Agent

- Responsibility: Resolve OS update and driver regression issues.
- Inputs: Recent updates, driver versions, rollback availability.
- Outputs: Regression likelihood, rollback path, compatibility guidance.
- Tools used: Update playbooks, driver compatibility matrix.
- Prompt strategy: Tie symptom start time to update timeline.
- Example behavior: Identifies problematic optional GPU driver update and recommends rollback.

---

## 4. Tech Stack

| Layer | Primary Choice | Alternatives | Why |
|---|---|---|---|
| Frontend | React web app | Streamlit for fast demo | React scales for production; Streamlit speeds hackathon iteration |
| Backend API | FastAPI | Flask | Async performance, schema validation, clear OpenAPI |
| Agent Runtime | Microsoft Agent Framework style | LangGraph | Strong multi-agent orchestration pattern |
| LLM Routing | OpenAI GPT + Gemini fallback | Local model via Ollama | Reliability plus cost/performance control |
| Retrieval | Chroma | FAISS | Fast local vector retrieval, easy hackathon setup |
| Primary Storage | SQLite | PostgreSQL | SQLite is simple for MVP, PostgreSQL for scale |
| Session Cache | In-memory or Redis | SQLite-only | Low-latency session state |
| Observability | OpenTelemetry + structured logs | Basic logging | Traceability and evaluation |
| Packaging | Docker | Native deployment | Portable, repeatable environments |
| Cloud Target | Azure App Service or Container Apps | VM | Managed production route |

### Model Routing Policy

1. Use smaller model for triage and question generation.
2. Use stronger model for diagnosis and remediation.
3. Use fallback model on timeout or quota limits.
4. Log model choice per turn for audit and optimization.

---

## 5. Complete Folder Structure

```text
system-doctor-ai/
  apps/
    web/
      src/
      public/
      package.json
    streamlit/
      app.py
  agents/
    orchestrator/
      controller.py
      policy.py
    triage/
      triage_agent.py
    question_engine/
      question_agent.py
    diagnosis_engine/
      diagnosis_agent.py
      confidence.py
    remediation/
      remediation_agent.py
    verification/
      verification_agent.py
    specialists/
      hardware/
        agent.py
      software/
        agent.py
      windows/
        agent.py
      macos/
        agent.py
      linux/
        agent.py
      bios_boot/
        agent.py
      update_driver/
        agent.py
  knowledge/
    decision_trees/
      boot_issues.json
      update_failures.json
    troubleshooting_playbooks/
      windows/
      macos/
      linux/
    command_catalog/
      windows_commands.json
      macos_commands.json
      linux_commands.json
    hardware_fault_matrix/
      faults.json
  prompts/
    system/
      orchestrator.md
      triage.md
    specialists/
      hardware.md
      software.md
      windows.md
      macos.md
      linux.md
      bios_boot.md
      update_driver.md
    safety/
      command_policy.md
      confirmation_policy.md
  packages/
    schemas/
      session.py
      diagnosis.py
      remediation.py
    shared_utils/
      logging.py
      retrieval.py
      normalization.py
  eval/
    datasets/
      benchmark_cases.jsonl
    judges/
      diagnosis_judge.py
      remediation_judge.py
    reports/
      latest_report.md
  tests/
    unit/
    integration/
    e2e/
  infra/
    docker/
      Dockerfile.api
      Dockerfile.web
      docker-compose.yml
    azure/
      bicep/
      deployment_notes.md
  .foundry/
    agent-metadata.yaml
    datasets/
    evaluators/
    results/
  .env.example
  pyproject.toml
  requirements.txt
  README.md
```

### Folder Explanations

- apps: User-facing interfaces for production web and quick demo streamlit app.
- agents: Multi-agent business logic and orchestration.
- knowledge: Structured troubleshooting intelligence and OS command base.
- prompts: Versioned prompt assets for all agents and guardrails.
- packages: Shared schemas and reusable utilities.
- eval: Test cases, judges, and evaluation outputs.
- tests: Automated quality checks at unit, integration, and end-to-end levels.
- infra: Docker and cloud deployment assets.
- .foundry: Foundry-ready metadata and evaluation artifacts.

---

## 6. Working Flow (Step-by-Step)

1. User input: user submits free-text issue plus optional OS and device info.
2. Triage classification: triage agent tags category, severity, and missing critical fields.
3. Adaptive questioning: question engine asks highest-information question each turn until stop criteria.
4. Diagnosis ranking: diagnosis engine returns top-3 root causes with confidence.
5. Fix generation: remediation agent maps top diagnosis to risk-aware fix steps by OS.
6. Verification loop: verification agent checks outcome; unresolved cases loop back.
7. Final report: ranked causes, completed and pending actions, warnings, and escalation path.

### Core API Contract Example

```json
{
  "session_id": "abc123",
  "input": "My laptop restarts randomly after update",
  "os": "windows",
  "answers": [
    {"q": "Does it restart under heavy load?", "a": "Yes"}
  ]
}
```

---

## 7. MVP Scope (Hackathon Build Plan)

### Build in 3-5 Days

1. Multi-agent skeleton with orchestrator, triage, question, diagnosis, remediation, verification.
2. Three specialists initially: Windows, Hardware, Update/Driver.
3. Knowledge layer with 50-100 curated playbook entries.
4. Confidence-scored top-3 diagnosis output.
5. Safe remediation with risk labels.
6. Basic verification loop and final report.
7. Streamlit UI or simple web chat UI.
8. SQLite session storage and structured logs.

### Skip for MVP

1. Fully autonomous command execution on user device.
2. Advanced screenshot or raw-log ingestion pipelines.
3. Full multi-region cloud rollout.
4. Enterprise-grade auth and RBAC complexity.

### Polish for Demo

1. Fast first response under 2-3 seconds.
2. Clean report card with confidence and rationale.
3. One strong end-to-end scenario per OS.
4. Safety confirmations before risky actions.
5. Demo script with before and after outcome.

### Suggested Day Plan

| Day | Focus |
|---|---|
| Day 1 | Scaffold, API, session state, triage |
| Day 2 | Question engine, diagnosis engine, Windows specialist |
| Day 3 | Hardware and update specialist, remediation playbooks |
| Day 4 | Verification loop, UI polish, logging, tests |
| Day 5 | Demo hardening, metrics summary, pitch rehearsal |

---

## 8. Example Prompt Templates

### Triage Prompt

```text
Role: Triage agent for SystemDoctor AI.
Task: Classify issue into one primary and one secondary category.
Allowed categories: hardware, software, windows, macos, linux, bios_boot, update_driver, network, storage, performance.
Input:
- User issue text
- Known OS
- Known recent changes
Return JSON:
{
  "primary_category": "...",
  "secondary_category": "...",
  "severity": "low|medium|high|critical",
  "missing_fields": ["..."],
  "triage_confidence": 0.0
}
Constraints:
- Do not provide fixes.
- Ask only for missing critical facts.
```

### Question Generation Prompt

```text
Role: Adaptive Question Engine.
Goal: Maximize diagnostic information gain with minimum questions.
Given:
- Current hypotheses with confidence
- Missing evidence fields
- Prior user answers
Return one best question and why it matters.
Return JSON:
{
  "question": "...",
  "why": "...",
  "target_hypothesis": "...",
  "expected_information_gain": 0.0
}
Rules:
- One question only.
- Avoid repeated or vague questions.
- Keep wording simple for non-technical users.
```

### Diagnosis Prompt

```text
Role: Diagnosis Engine.
Task: Produce top 3 root causes with calibrated confidence.
Given:
- Session evidence
- Specialist findings
- Retrieved knowledge snippets
Return JSON:
{
  "diagnoses": [
    {
      "name": "...",
      "confidence": 0.0,
      "supporting_evidence": ["..."],
      "conflicting_evidence": ["..."]
    }
  ],
  "needs_more_data": true
}
Rules:
- Confidence values sum to <= 1.0.
- If uncertainty is high, set needs_more_data=true.
```

### Fix Generation Prompt

```text
Role: Remediation Agent.
Task: Create safe ordered fix steps for selected diagnosis and OS.
Input:
- Selected diagnosis
- OS
- User skill level
- Safety policy
Return JSON:
{
  "risk_label": "low|medium|high|critical",
  "steps": [
    {
      "step_no": 1,
      "action": "...",
      "command": "...",
      "rollback": "...",
      "checkpoint": "..."
    }
  ],
  "estimated_time_minutes": 0
}
Rules:
- Prefer non-destructive actions first.
- Provide rollback for medium+ risk actions.
- Never assume admin access without asking.
```

### Safety Prompt

```text
Role: Safety Guard.
Task: Evaluate each proposed action for risk and permission.
Input: action, command, OS, diagnosis confidence
Output JSON:
{
  "allow": true,
  "risk_label": "low|medium|high|critical",
  "requires_confirmation": true,
  "warning": "...",
  "blocked_reason": "..."
}
Policy:
- Block destructive disk, firmware flashing, and exposed-network commands without explicit consent.
- Require high-confidence diagnosis or manual override for high-risk actions.
```

---

## 9. Data and Knowledge Layer Design

### Decision Trees
Use deterministic symptom trees for high-signal flows like boot failure, blue screen, panic, and update regressions.

### Troubleshooting Playbooks
Store each playbook with:

1. Preconditions.
2. Ordered steps.
3. Expected checkpoints.
4. Rollback path.
5. Escalation condition.

### Command Catalog
Store OS-scoped safe commands with metadata:

1. Privilege level.
2. Side effects.
3. Reversible or irreversible.
4. Validation command.

### Hardware Fault Matrix
Map symptom signatures to hardware probabilities, for example:

1. Reboot under load -> PSU or GPU or thermal.
2. Clicking noise + slow I/O -> storage failure.
3. No display + beep pattern -> RAM or GPU or motherboard issue.

### Example Decision Tree Node

```json
{
  "id": "boot_001",
  "question": "Does the system show manufacturer logo?",
  "if_yes": "boot_002",
  "if_no": "bios_001",
  "signals": ["display_path", "firmware_path"]
}
```

### Example Playbook

```json
{
  "playbook_id": "win_driver_rollback_01",
  "os": "windows",
  "diagnosis": "gpu_driver_regression",
  "risk_label": "medium",
  "steps": [
    {"n": 1, "action": "Open Device Manager", "checkpoint": "GPU listed"},
    {"n": 2, "action": "Rollback driver", "checkpoint": "System stable for 15 min"}
  ],
  "rollback": "Reinstall last stable driver package",
  "escalate_if": "display crash persists after rollback"
}
```

---

## 10. Safety and Guardrails

### Command Safety Policy

| Risk | Examples | Policy |
|---|---|---|
| Low | Read-only diagnostics | Run without extra confirmation |
| Medium | Driver rollback, service restart | Ask confirmation once |
| High | BIOS settings change, bootloader repair | Double confirmation + warning |
| Critical | Firmware flashing, partition operations | Block by default, require explicit override flow |

### Harm Prevention Rules

1. Never output destructive commands without warning and alternatives.
2. Never claim certainty when evidence is incomplete.
3. Always provide backup or rollback guidance before risky actions.
4. Always present service-center escalation for hardware danger signs.
5. Always require user confirmation before high or critical actions.

### Confirmation System

1. Show action summary.
2. Show risk label and impact.
3. Ask explicit consent.
4. Log consent timestamp.
5. Reconfirm if context changes.

---

## 11. Evaluation Strategy

### Core Metrics

1. Top-1 Diagnosis Accuracy: Acc@1.
2. Top-3 Diagnosis Accuracy: Acc@3.
3. Remediation Success Rate.
4. Question Efficiency (average turns to target confidence).
5. Safety Compliance Rate.
6. User Satisfaction score.

### Test Dataset Strategy

1. Build labeled cases for Windows, macOS, Linux.
2. Balance hardware and software categories.
3. Include ambiguous/conflicting symptom cases.
4. Include adversarial safety cases.

### Feedback Loop

1. Capture user outcome after each session.
2. Compare predicted diagnosis vs confirmed cause.
3. Update playbooks and confidence calibrator weekly.
4. Track regressions with versioned evaluation reports.

### MVP Targets

1. Acc@3 >= 0.80 on curated benchmark.
2. Safety compliance >= 0.98.
3. Median diagnosis turn count <= 6 questions.

---

## 12. Deployment Plan

### Local Deployment (Streamlit + FastAPI)

```bash
# API
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Streamlit UI
streamlit run apps/streamlit/app.py --server.port 8501
```

### API Deployment (FastAPI)

1. Containerize API.
2. Deploy container to managed runtime.
3. Set environment variables for model providers and retrieval paths.
4. Enable HTTPS, health checks, and request logging.

### Docker Compose Sample

```yaml
version: "3.9"
services:
  api:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.api
    ports:
      - "8000:8000"
    env_file:
      - .env
  web:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.web
    ports:
      - "3000:3000"
    depends_on:
      - api
```

### Optional Azure Foundry Integration

1. Maintain .foundry metadata and eval artifacts.
2. Keep prompts and evaluation bundles versioned.
3. Route model calls through provider abstraction.
4. Add telemetry linking session traces to eval outcomes.
5. Use managed identity and secure secret storage in production.

### Production Hardening Checklist

1. Rate limiting and abuse protection.
2. Structured audit logs for actions and confirmations.
3. PII-safe logging policy.
4. Backup and retention for session reports.
5. Canary rollout for prompt and playbook updates.

---

## 13. Future Enhancements

1. Voice-first troubleshooting assistant.
2. Screenshot and error-dialog analysis.
3. Automatic log ingestion and parsing.
4. Device telemetry connectors for richer diagnosis.
5. Semi-autonomous repair mode with user approvals.
6. Human-in-the-loop escalation console.
7. Device reliability score and proactive recommendations.
8. Continuous learning from confirmed outcomes.

---

## Final Notes for Hackathon and Production Roadmap

1. Start with a narrow but reliable scope, then expand specialist coverage.
2. Prioritize explainability and safety over aggressive automation.
3. Use evaluation reports in your demo to show engineering rigor.
4. Position as high-confidence diagnosis plus verification loop, not guaranteed certainty.
5. Demonstrate one complete success journey per OS for judges.
