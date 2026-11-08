# ResumeIQ matching-model training

The application starts with an explainable hybrid baseline. The supervised ranker is opt-in and must be trained only on recruiter-reviewed candidate/job relevance pairs.

## Dataset

Copy `data/labeled_match_pairs.template.csv` to `data/labeled_match_pairs.csv`. Add one row per candidate/job pair. Use `label=1` for a reviewed relevant match and `label=0` for a reviewed non-match. Use pseudonymous IDs and remove unnecessary personal information.

Required columns: `candidate_id`, `job_id`, `candidate_text`, `job_text`, `candidate_skills`, `required_skills`, `label`.

Skill list fields accept JSON arrays or pipe-separated values. Optional fields include `preferred_skills`, `candidate_experience`, `minimum_experience`, `maximum_experience` and `education_match` (0–1).

Do not train on protected attributes or proxies for protected characteristics. Do not turn historic hiring outcomes into labels without auditing them for bias and consistency.

## Train and evaluate

From the project root in PowerShell:

```powershell
cd training
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python train_ranker.py
```

The trainer requires at least 50 labelled pairs and 10 distinct candidate groups, then uses `GroupShuffleSplit` by candidate ID to avoid candidate leakage. It reports accuracy, precision, recall, F1, ROC-AUC, average precision, Brier score, confusion matrix and NDCG@5 by job.

The model candidate is written to `backend/app/models/artifacts/match_ranker.joblib`, and the evaluation report is written to `training/reports/latest_metrics.json`. A hold-out evaluation is not evidence of general hiring accuracy. Validate on representative data from multiple job families and time periods before promotion.

After reviewing the report and training-data provenance, set `USE_TRAINED_MODEL=true` and restart the backend. Keep the baseline as the fallback. Never promote a model based only on training-set metrics.
