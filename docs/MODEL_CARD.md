# Pilot mistake classifier model card

## Purpose

Suggest one likely mistake category for a failed basic Python teaching task.
It is not a general debugger, proof of correctness, grading authority or hiring model.

## Data provenance

240 programmatically generated code mutations, from 24 source families authored
for this package. Ten samples per family change variable names, not semantics.
Every sample has one witness test that passes on the reference and fails on the
mutant. Those checks ran during generation. Labels describe the authored mutation;
they have **not** undergone independent human review. All `human_reviewed` flags
are false. No real student records, public scraped CVs or external datasets are used.

Categories: wrong_condition, loop_boundary, wrong_update, missing_edge_case.
Some real bugs fit multiple categories. The current single-label model cannot
represent multiple simultaneous faults. A return statement in the wrong place,
for example, may not fit the training set well.

## Training

Character n-gram TF-IDF (2-5 characters, maximum 12,000 features) plus Logistic
Regression with balanced class weights. Linear SVM uses the same pipeline as
a comparison. Features contain source code and observed runtime error types;
they never include the label, family ID or expected answer. Runtime errors are
available at inference, but their relationship to synthetic labels can make
performance appear stronger than general code understanding.

## Split and results

Train: 16 source families / 160 rows. Validation: 4 / 40. Test: 4 / 40.
Each split contains all four labels. Renamed versions remain in one split.
Only four semantic test families exist: 40 rows are NOT 40 independent programs.
Some train/test programs share patterns even though source-family IDs differ.

On the delivered run (scikit-learn 1.8.0):

| Model | Test accuracy | Test macro-F1 | Test macro recall |
| --- | --- | --- | --- |
| Logistic Regression | 0.725 | 0.6535 | 0.725 |
| Linear SVM | 0.750 | 0.6667 | 0.750 |

Both validation scores are 1.0 on this small, synthetic validation set. That
does not establish real-world reliability. In particular, the held-out wrong_update
family is misclassified, showing a clear generalisation weakness. Metrics are
reported as observed; the app does not replace them with invented improvements.

## Inference policy

Logistic Regression was selected before evaluation because it provides class
scores; these are **not calibrated** probabilities of a diagnosis being correct.
Scores below 0.45 yield "uncertain". This threshold is a pilot heuristic, not a
validated safety bound. Above-threshold mistakes and out-of-distribution inputs
can still be misclassified. Always show actual tests alongside the prediction.

Syntax errors and unsupported features are handled by the parser/runner, not ML.
All-tests-passed feedback is based on execution evidence, not a learned label.

## Next research work

Obtain consenting students' attempts, anonymise records, use two reviewers for
mistake labels, document disagreements and group splits by student and task.
Collect examples outside the four current categories. Evaluate on an untouched
real test set, including abstention coverage and per-class recall, before making
claims about general performance. Do not automatically promote user feedback
to ground-truth labels.
