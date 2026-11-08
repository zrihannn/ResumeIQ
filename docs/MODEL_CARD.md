# ResumeIQ matching model card

## Intended use

ResumeIQ produces role-relevance estimates to help a recruiter review candidate profiles against a specific job description. It is not designed to predict job performance, make hiring decisions, infer protected characteristics, or automatically reject candidates.

## Current default

The default engine is a deterministic hybrid baseline combining:

- Required and preferred skill coverage from canonical skill names.
- TF-IDF text similarity between job-related candidate evidence and the role description.
- Experience-range fit, with uncertainty when experience cannot be estimated.
- Education degree/field-of-study relevance, with uncertainty when the profile lacks education data.

The current baseline component weights are 45% skills, 30% lexical text relevance, 15% experience fit and 10% education context. These are transparent heuristic weights, not statistically learned parameters or calibrated probabilities.

The engine excludes candidate names and employer identities from its text-similarity input. Certification names, achievement text, publication text and relevant role/project evidence may contribute to semantic relevance. The system reports component estimates and plain-language reasons. The overall number is a heuristic relevance score, not a calibrated probability.

## Optional supervised ranker

A Logistic Regression candidate/job pair classifier can be trained from human-reviewed labels. Training is disabled by default and requires a local labelled dataset. Candidate groups are held out together to reduce candidate leakage between train and test partitions. The pipeline reports classification, calibration and ranking metrics, but model promotion is manual.

No trained model artifact or claimed model-performance result is included in this repository. A temporary synthetic-data smoke test has been used only to exercise the training script and is not evidence of model quality.

## Data requirements

Training labels should be adjudicated by qualified reviewers using a documented job-specific rubric. Store only data with an appropriate legal basis and approved retention period. Prefer pseudonymous candidate IDs and de-identified text where feasible. Keep label rationale and provenance outside public artefacts.

## Evaluation before promotion

Before enabling a trained ranker, require:

1. Documented dataset provenance, consent/legal basis and data-retention controls.
2. Job-family-aware and time-aware evaluation, with candidate groups isolated across splits.
3. Precision@K, Recall@K, NDCG@K and relevant classification/calibration metrics.
4. Error analysis for job families, experience bands, education paths and other legally permissible audit groups.
5. Human review of false positives, false negatives and explanation faithfulness.
6. A versioned model artifact, rollback procedure and reproducible training report.

## Limitations and risks

- Resume extraction can omit, misread or incorrectly associate fields, especially in complex layouts or scanned files.
- TF-IDF is lexical rather than deep semantic understanding; related concepts without word overlap can be missed.
- The supervised model is only as reliable as its labels and evaluation design.
- Historical hiring outcomes can encode past bias and should not be treated as neutral ground truth.
- Education and experience signals can unfairly penalize non-traditional career paths if applied rigidly.
- Resume text may contain irrelevant personal information. The product should minimize access and avoid using sensitive attributes for ranking.

## Human oversight

Recruiters must inspect the resume and supporting evidence, correct parser errors, consider context not represented in the score, and make decisions independently. Missing information must not be interpreted as proof that a candidate lacks a qualification.
