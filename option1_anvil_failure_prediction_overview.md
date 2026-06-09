# Option 1: Early HPC Job Failure Prediction (Anvil)

## One-Sentence Concept
Build a model that predicts whether an HPC job on **Anvil** will **fail or time out** using **job metadata** and **early resource-usage telemetry**.

## Why This Option
This option aligns well with the GSC prompt:
- **resource usage analysis**,
- **event prediction**,
- **real operational value**,
- a clear and accessible **data science task**.

It is also supported by recent FRESCO findings:
- **cross-cluster transfer is not reliable**,
- **local, site-specific modeling is the defensible approach**,
- **temporal splits and leakage-aware evaluation matter**.

## Core Task
Given information available **early in a job’s execution**, teams predict whether that job will:
- complete successfully, or
- end in **failure or timeout**.

In simple terms:
> Use early telemetry to identify jobs likely to go wrong before they finish.

## Recommended Dataset Scope
- **Single cluster:** Anvil only
- **Why one cluster:** avoids cross-cluster measurement mismatch and keeps the challenge focused on prediction rather than transfer artifacts
- **Why Anvil:** strong volume/density of usable data for robust training and evaluation

## Inputs to Teams
Teams would receive features such as:
- requested cores
- requested hosts
- timelimit
- queue/partition
- submit/start timing
- early CPU usage
- early memory usage
- early I/O or related telemetry summaries

Recommended packaging:
- provide **precomputed early-window features** rather than raw telemetry streams

## Prediction Setting
The challenge should make prediction-time constraints explicit:
- teams only use information available **at prediction time**
- no full-run summaries
- no post-failure signals
- no direct label proxies

This keeps the task realistic and avoids leakage.

## Target Label
**Primary label:**
- `failure_or_timeout` (binary)

This is the cleanest main target because it is:
- concrete,
- easy to explain,
- operationally meaningful,
- easier to score than a more subjective “slowdown” label.

## Possible Secondary Label
**Optional secondary/bonus task:**
- `slowdown`

Recommendation:
- keep slowdown **secondary**, not primary, unless a very defensible definition is available.

## Evaluation
Teams submit a **risk score or probability** that a job will fail.

Recommended metrics:
- **Primary:** AUPRC
- **Secondary:** AUROC

### Metric intuition
- **AUPRC** rewards finding failed jobs without too many false alarms; best when failures are rare.
- **AUROC** measures how well the model ranks failed jobs above non-failed jobs.

## Train/Test Design
Recommended split:
- **train:** older Anvil time period
- **validation:** later period
- **hidden test:** newest period

Important principle:
- use **temporal splits**, not random splits

## Why This Is a Strong Challenge Option
- clear problem statement
- easy to explain to students and judges
- realistic operations use case
- grounded in real FRESCO research
- avoids the complexity of cross-cluster transfer
- supports automated leaderboard grading

## Main Risks / Design Choices
Still to decide:
- exact early prediction window (for example, first 5, 10, or 15 minutes)
- exact failure label mapping from scheduler exit states
- whether slowdown is included at all
- exact feature set released to participants

## Recommended High-Level Framing
> Participants will build an early-warning model for HPC jobs on Anvil. Using submission metadata and early resource-usage telemetry, they must predict which jobs are likely to fail or time out before completion.

## Bottom Line
This option is currently the strongest candidate for a first challenge concept:
- **Anvil only**
- **job-level prediction**
- **early telemetry + metadata**
- **failure/timeout as the main target**
- **AUPRC-led evaluation with temporal splits**
