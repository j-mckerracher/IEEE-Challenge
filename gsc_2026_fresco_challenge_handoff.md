# GSC 2026 FRESCO Challenge Handoff

Date: 2026-06-08

## Context

IEEE Computer Society Global Student Challenge 2026 includes a challenge prompt titled:

> Analyzing Resource Usage in Data Center Computers and Predicting Events (i.e. Failures or Performance Slowdowns)

Josh has been asked to create one of the three competition challenges. The goal is to design a challenge grounded in recent FRESCO research while staying tightly aligned with the published prompt.

FRESCO research context:

- FRESCO is a multi-institution HPC/data-center telemetry dataset covering Anvil, Conte, and Stampede.
- It links job metadata, scheduler information, resource requests, runtime behavior, and telemetry such as CPU, memory, I/O, and related metrics.
- Recent work found that cross-cluster memory prediction does not robustly generalize, but local telemetry modeling and operational prediction remain promising.
- Earlier FRESCO analyses found anomaly scores correlated with job failures, timelimit strongly influenced runtime prediction, and leakage-aware/user-aware/temporal evaluation is important.

## Key Decision

Telemetry cleaning/provenance should not be the main challenge.

It is relevant to FRESCO, but it does not directly match the GSC prompt unless framed as detecting data-quality incidents. It can be included as a robustness wrinkle or hidden validation issue, but the headline task should be event prediction from resource usage.

The strongest aligned directions are:

1. Early warning from partial telemetry.
2. Job failure prediction from resource usage.
3. Cluster health event forecasting.
4. Performance slowdown detection.
5. Queue congestion / scheduling slowdown forecasting.

## Recommended Challenge Direction

### Primary Recommendation: Early Warning From Partial Telemetry

Students receive job metadata plus early resource-usage telemetry and must predict whether the job will later fail or experience a performance slowdown.

This is the best overall fit because it combines:

- resource usage analysis,
- event prediction,
- operational value,
- a clear data-science task,
- strong connection to FRESCO findings.

Possible challenge title:

**Predicting Failures and Slowdowns from Early Data-Center Telemetry**

Core story:

> A data-center operator wants to identify jobs likely to fail or slow down while there is still time to intervene. Given submission metadata and early resource-usage signals, teams must predict future adverse events and explain the signals behind their alerts.

## Candidate Challenge Designs

### Option 1: Early Warning From Partial Telemetry

Task:

- Predict eventual failure, timeout, or slowdown using only submission metadata and early telemetry.

Inputs:

- Job metadata: requested cores, hosts, timelimit, cluster/partition class, submission/start timing.
- Early telemetry: first N minutes or first X% of observed CPU, memory, I/O, NFS, block usage.
- Optional aggregate context: recent cluster load or queue pressure.

Labels:

- Binary: adverse event vs normal.
- Or multi-class: normal, failed, timeout, slowdown.

Scoring:

- AUPRC for rare adverse events.
- AUROC as secondary.
- Recall at fixed false-positive rate.
- Calibration score for alert probability.
- Optional lead-time bonus if teams predict earlier using shorter windows.

Why it works:

- Directly aligned with failures/slowdowns.
- Uses resource usage as the primary signal.
- Feels like a real operations problem.

Risk:

- Requires careful construction of early telemetry windows.
- Need to avoid leakage from post-event or full-job summary features.

### Option 2: Job Failure Prediction From Resource Usage

Task:

- Predict whether a job will fail or terminate abnormally.

Inputs:

- Job request fields.
- Runtime/resource summaries.
- Optional early telemetry subset.

Labels:

- Success vs failure.
- Could include failure classes if labels are reliable.

Scoring:

- AUPRC, because failures may be imbalanced.
- F1 or recall at operational false-alert budget.
- Confusion matrix by job size/workload group.

Why it works:

- Cleanest and easiest to grade.
- Directly matches the word “failures.”
- Prior FRESCO anomaly analysis found top anomalies had much higher failure rates.

Risk:

- If using full-job summary telemetry, the challenge may become less “early warning” and more postmortem classification.
- Failure labels must be clean and consistently defined.

### Option 3: Cluster Health Event Forecasting

Task:

- Predict future time windows with elevated failure rate, slowdown rate, or congestion from recent aggregate resource usage.

Inputs:

- Hourly or sub-hourly aggregate telemetry:
  - job arrivals,
  - requested cores/memory/time,
  - observed CPU/memory/I/O,
  - queue depth proxies,
  - recent failure/timeout counts if allowed.

Labels:

- Next-window high failure-rate event.
- Next-window high slowdown-rate event.
- Next-window congestion event.

Scoring:

- Event forecast AUPRC.
- Lead-time-weighted score.
- False-alert penalty.
- Calibration.

Why it works:

- Strongest “data center computers” framing.
- Avoids needing exact per-node hardware failure logs.
- Useful for operational dashboards and alerts.

Risk:

- FRESCO is job-centric, not necessarily node-health-centric.
- Event definition must be constructed carefully from available labels.

### Option 4: Performance Slowdown Detection

Task:

- Predict whether a job is unusually slow relative to comparable jobs.

Inputs:

- Job metadata.
- Resource usage telemetry.
- Workload cohort features.

Labels:

- Slowdown derived from residuals against baseline runtime model.
- Or percentile-based label within comparable cohorts.

Scoring:

- AUPRC/F1 for slowdown class.
- Calibration.
- Robustness across workload groups.

Why it works:

- Directly matches “performance slowdowns.”
- Uses FRESCO’s runtime and resource usage structure.

Risk:

- Slowdown is not a native label and must be defined defensibly.
- Poor label design could make the challenge feel arbitrary.

### Option 5: Queue Congestion / Scheduling Slowdown Forecasting

Task:

- Predict future queue congestion or severe wait-time class.

Inputs:

- Recent submission volume.
- Requested cores/hosts/timelimit.
- Cluster/partition metadata.
- Historical queue wait patterns.

Labels:

- Job-level wait class: `<10 min`, `10 min-1 hr`, `1-6 hr`, `>6 hr`.
- Or time-window congestion class.

Scoring:

- Macro-F1 for wait classes.
- MAE for wait time.
- Calibration for long-wait probability.

Why it works:

- Practical and intuitive.
- Labels are easier to define than slowdown labels.
- Fits “performance slowdown” if framed as scheduling/service slowdown.

Risk:

- Less directly about computer hardware/resource telemetry and more about scheduler behavior.

## Suggested Final Challenge Specification

Use a two-part challenge:

1. **Primary task:** early adverse-event prediction.
2. **Secondary analysis:** explain resource-usage signals and recommend an alerting policy.

This gives students a clear leaderboard task while still rewarding operational insight.

Recommended official task:

> Given job metadata and early resource-usage telemetry, predict whether each job will later fail, timeout, or run anomalously slowly. Teams must submit event probabilities and a short report explaining which resource patterns drive their predictions and how a data-center operator should use the alerts.

Recommended labels:

- `event_failure_or_timeout`: binary.
- `event_slowdown`: binary, derived from runtime residual or cohort percentile.
- `event_adverse`: union of failure/timeout/slowdown.

Recommended primary target:

- `event_adverse`.

Recommended secondary targets:

- failure/timeout separately,
- slowdown separately.

## Grading Proposal

Automated leaderboard:

- 40% adverse-event AUPRC.
- 20% recall at fixed false-positive rate.
- 15% calibration / Brier score.
- 15% subgroup robustness across job size, cluster, and workload class.
- 10% reproducibility checks.

Human/judge review:

- Explanation quality.
- Correct handling of leakage.
- Operational usefulness of alert thresholds.
- Clarity of assumptions and limitations.

Important grading principle:

- Do not reward models that use features unavailable at prediction time.
- Make prediction-time feature availability explicit.
- Penalize leakage, especially full-runtime fields or post-event summaries if the task is early warning.

## Dataset Packaging Notes

Recommended split:

- Train: older time period.
- Public validation: later time period, visible labels.
- Hidden test: newest time period or different cluster/time slice.

Recommended files:

- `train.csv`
- `validation.csv`
- `test.csv`
- `sample_submission.csv`
- `data_dictionary.md`
- `evaluation.py`
- `baseline_model.ipynb` or `baseline_model.py`

Recommended feature families:

- Submission/request features:
  - requested cores,
  - requested hosts,
  - timelimit,
  - queue or partition class if safe,
  - submit/start timing.
- Early telemetry features:
  - CPU usage summaries,
  - memory usage summaries,
  - I/O/NFS/block summaries,
  - early trend/slope features.
- Context features:
  - recent load,
  - recent queue pressure,
  - recent failure/slowdown rate, if available and not leakage.

Exclude or hide:

- final runtime if predicting early slowdown,
- exit code if predicting failure,
- full-job peak memory if not available at prediction time,
- direct label proxies,
- raw user IDs unless intentionally used in a leakage lesson.

## FRESCO-Specific Guardrails

The challenge should reflect lessons from the research:

- Use temporal splits, not random splits, to avoid inflated performance.
- Avoid user leakage unless the challenge explicitly includes a leakage-detection component.
- Be explicit about cluster/source fields and units.
- Treat cross-cluster generalization as optional robustness, not the core leaderboard requirement, unless the dataset is designed for it.
- If using memory labels, avoid claiming cross-cluster semantic equivalence unless measurement semantics are clearly documented.
- Keep the problem achievable for teams of two students who are also solving two other GSC prompts.

## Best Framing for the Organizers

Recommended pitch:

> This challenge asks students to build an early-warning model for adverse events in data-center/HPC jobs using real resource-usage telemetry. Teams will analyze CPU, memory, I/O, scheduling, and workload signals to predict failures, timeouts, or severe slowdowns before they occur. The challenge emphasizes both predictive accuracy and operational trustworthiness: models must avoid leakage, work under realistic temporal evaluation, and provide interpretable alerting guidance.

## Open Decisions

Need to decide before implementation:

- Whether the main unit is job-level prediction or time-window cluster-health prediction.
- Whether slowdown is included as a primary label or only as a bonus/secondary label.
- Whether teams receive raw time-series telemetry or precomputed early-window features.
- Whether the hidden test evaluates same-cluster temporal generalization or cross-cluster robustness.
- How much data can be safely released publicly after anonymization.

## Recommendation

Start with **job-level early adverse-event prediction** using precomputed early-window telemetry features.

This is the best balance of:

- prompt alignment,
- student accessibility,
- automated grading,
- operational realism,
- FRESCO research relevance.

Use telemetry cleaning/provenance only as a small robustness concern in the data dictionary and grading rubric, not as the primary challenge.
