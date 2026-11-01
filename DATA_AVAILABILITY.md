# Data availability

This release provides anonymous derived profiles, constructed applications and the saved evaluations needed to reproduce the prototype's portfolio comparisons.

| Material | Origin and observation unit | Included in this repository | Access and interpretation |
| --- | --- | --- | --- |
| Reviewer profiles | Five scholars; five historical publications per scholar in the development corpus, with a December 2018 cutoff | Anonymous IDs, topic and method keywords with distinct-paper frequencies, field shares and profile summaries | Derived knowledge profiles, not actual human review records. Original publications and identifying packets are retained in the research archive. |
| Applications | Ten fictional full applications, organized as five matched topic pairs | Application text, disciplinary composition and contribution-target specification | Constructed materials based on NSFC application structure; not confidential NSFC submissions. |
| Reference values | One value per application, calculated from supported contribution targets and importance weights fixed before review | Component values, importance weights, target mapping and sensitivity calculations | Measures contributions supported by the constructed design. Independent scientific assessment remains planned. |
| AI reviews | Fifty agent–application pairs | Criterion ratings, categories, supporting quotations and explanations | Saved outputs from the recorded development run; not human reviews. |
| AI rankings | Five agents, each ranking all ten projects separately | Complete submitted rankings | Earlier criterion scores were withheld. |
| Joint fits | Four solvers under two ranking-input conditions | Frozen matrices, fitted R objects, parameters, orders and logs | R 4.5.2; rankrate 1.2.1. Reference values do not enter fitting. |
| Portfolio comparisons | Procedure × funding capacity, for capacities one through nine | Selections, reference-value totals, loss and loss per funded project | Recomputed from the saved evaluations and fits. |
| Numerical benchmark | Three reviewers with 18, 30 or 100 projects; reported 300-replication benchmark | Description and aggregate results in the appendix | Original coauthor simulation code and per-replication records are not included. |
| Human validation | Corresponding scholars reviewing matched experimental materials | Design in the appendix | Planned; no human participant data are included. |

## Input boundaries

Agent inputs exclude project reference values, contribution-target codes and the optimal portfolio. The protocol utility builds requests from the public derived profiles. These requests replace the original publication packets, so new model responses constitute a new experiment.

The field-distance matrix uses a fixed development corpus of 25 publications. It is released with the derived calculation vectors and is not presented as a universal disciplinary geometry.

## Provenance

`source_run_provenance.json` records hashes of the original internal data files. `manifest.json` records hashes of the released files. The former identifies the research input archive; the latter verifies this public package.

Names, email addresses, private credentials and original publication packets are not needed to reproduce the released portfolio analysis and are not included.
