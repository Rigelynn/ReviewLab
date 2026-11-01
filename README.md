# ReviewLab

**GenAI review experiments for selecting interdisciplinary research projects.**

ReviewLab studies how organizations can combine expert evaluations to select valuable projects within a limited budget. Publication-based agents score constructed applications and separately rank the project pool. A Mallows–Binomial model combines these observations; the simulator compares its selections with averaging, voting, ranking and delegation under the same funding capacity.

[Open the interactive prototype](http://106.54.30.90:3389/reviewlab/) · [Short proposal](proposal.docx) · [Technical appendix](appendix.docx) · [Application materials](applications.docx)

## Start the simulator

The preview requires **Python 3.10 or later** and uses only the standard library. It runs locally without an API key or an R installation.

```bash
git clone https://github.com/Rigelynn/ReviewLab.git
cd ReviewLab
python3 -B cloud_server.py --port 3006
```

Open **http://127.0.0.1:3006/**. The interface has five modules:

| Module | What readers can examine |
| --- | --- |
| Scholar Simulation | Five anonymous publication-based profiles, research keywords and disciplinary breadth |
| Project Library | Ten constructed applications, disciplinary composition and predefined contribution targets |
| Review Experiment | Fifty saved review forms and five separately submitted priority rankings |
| Portfolio Selection | Selected projects, total reference value and selection loss as funding capacity changes |
| Mathematical Model | The scoring rules, project-value calculation and joint score–ranking model |

The interface loads the completed AI evaluations and recalculates portfolio outcomes. It does not send new LLM requests.

## What has been completed

The development experiment uses **five agents and ten applications**. The recorded underlying model is `deepseek-v4-pro-0813`, with temperature 0.3. Each agent independently rates novelty, scientific value and feasibility on a 1–5 scale. A separate request asks the same agent to rank all ten applications without seeing its earlier scores. Project reference values are withheld from both tasks.

We fitted the joint model with **FV, Greedy, GreedyLocal and ASTAR** in the official **rankrate 1.2.1** package, using **R 4.5.2**. The four algorithms solve the same statistical model. Four additional fits use score-derived orders in place of separately submitted rankings as a dependence check. All eight fitted objects and their input matrices are included.

At three funding slots, the saved evaluations give the following results:

| Procedure | Selected projects | Total reference value | Selection loss |
| --- | --- | ---: | ---: |
| Joint FV / Greedy / GreedyLocal / ASTAR | P01, P03, P07 | 2.6625 | 0.0000 |
| Mean scoring | P01, P05, P07 | 2.5250 | 0.1375 |
| Midpoint voting | P01, P05, P07 | 2.5250 | 0.1375 |
| Ranking derived from scores | P01, P03, P05 | 2.5375 | 0.1250 |
| Direct-ranking Borda | P01, P03, P07 | 2.6625 | 0.0000 |

Joint estimation and direct Borda select the same set at this capacity. These results demonstrate the workflow on one development pool. The corresponding-scholar comparison, independently checked contribution assessments and experiments with additional project pools remain planned.

## Reproduce the saved analysis

From the repository root:

```bash
python3 -B verify_artifact.py
python3 -B -m unittest discover -s tests -v
python3 -B genai_midpoint_voting.py --data-dir data/nsfc_panel_v3 --capacity 3
python3 -B research/rankrate_alignment/analyze_results.py
```

The tests check the saved score–ranking inputs, reject changed inputs when the saved R fits no longer apply, and verify portfolio arithmetic for funding capacities one through nine. The all-capacity comparison is stored in [comparison.csv](research/rankrate_alignment/comparison.csv).

For an R refit, install R 4.5.2 and the dependencies documented in [the fitting guide](research/rankrate_alignment/README.md), then run:

```bash
Rscript research/rankrate_alignment/fit_rankrate.R research/rankrate_alignment direct FV
Rscript research/rankrate_alignment/fit_rankrate.R research/rankrate_alignment direct Greedy
Rscript research/rankrate_alignment/fit_rankrate.R research/rankrate_alignment direct GreedyLocal
Rscript research/rankrate_alignment/fit_rankrate.R research/rankrate_alignment direct ASTAR
```

Replace `direct` with `score_derived` to reproduce the dependence checks. R fits use only the scores and rankings; reference values are read later to evaluate the selected portfolios.

## Materials and protocol

The [protocol directory](research/protocol/) documents the profile inputs, scoring and ranking prompts, and recorded model settings. Its offline request builder creates requests from the released, anonymous derived profiles and applications. Original publication packets are not redistributed; these public requests therefore support new experiments with the released profiles rather than exact regeneration of the original LLM responses.

The three criterion ratings are averaged after transformation to a 0–100 scale. Reverse-coded integer scores use support **M = 12**. The main voting rule is **S/M < 0.5**, equivalently **T > 50**; categorical funding recommendations and a configurable threshold are supplementary comparisons.

Each application's reference value is the importance-weighted proportion of predefined contribution targets supported by its design. It measures the constructed design's contributions, not a funded project's realized citation impact. The same values are used to evaluate every selection procedure.

## Repository contents

```text
proposal.docx, appendix.docx       Submission documents with editable equations
applications.docx                 Constructed application materials
web/                              Simulator interface
data/nsfc_panel_v3/                Derived profiles, applications and saved reviews
research/protocol/                Anonymous prompts, model settings and request builder
research/nsfc_instruments/         NSFC source-field mapping and research additions
research/rankrate_alignment/       Frozen matrices, R scripts, eight fits and comparisons
research/rankrate_source/          Unmodified rankrate source archive and provenance
tests/                            Reproducibility and protocol checks
```

The numerical benchmarks reported in the appendix are a separate experiment. This release includes their description and results, but not the coauthors' original simulation script or per-replication numerical data. The included R code refits the saved **GenAI** evaluations.

See [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md) for data provenance and observation units, and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for source attribution and licensing information.

## Research references

- Böttcher and Klingebiel (2025). [Organizational Selection of Innovation](https://doi.org/10.1287/orsc.2023.17357).
- Pearce and Erosheva (2022). [A Unified Model for Rankings and Scores](https://www.jmlr.org/papers/v23/21-1262.html). The official implementation is [rankrate](https://github.com/pearce790/rankrate).
- Tranchero et al. (2026). [Simulating Strategic Interactions with AI Agents](https://doi.org/10.1002/smj.70112).

This repository accompanies a proposed study. Human–AI validation results will be added after those experiments have been conducted.
