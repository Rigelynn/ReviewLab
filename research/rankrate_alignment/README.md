# GenAI review results with the numerical benchmark methods

This experiment refits 50 saved review forms and five separately submitted rankings. No new AI evaluations were requested. The original materials and project reference values are unchanged.

The coauthor numerical appendix identifies rankrate 1.2.1. Its original R simulation script was not supplied. We used the official author package, unchanged, with FV, Greedy, GreedyLocal and ASTAR. All eight fits completed under R 4.5.2. The runtime was the official r-base:4.5.2 image, digest sha256:c84d2d97cb9c4d895b219d83a5fd480302a6ad0d2fd449f3cda7978583909a02. Session records identify the installed package versions.

## Frozen inputs

There are five reviewers and ten applications. Each score is S=15 minus the sum of the three original 1–5 ratings, so M=12. The numerical benchmark uses M=10; the AI scale is preserved rather than rescaled.

Each row of a ranking file lists project column indices from most to least preferred. It does not list rank positions assigned to each project. The main fits use separately submitted AI rankings. A dependence check substitutes rankings derived from the same scores. Score ties use the project permutation frozen with seed 1028.

Reference values are held separately from the fitting inputs. The R program never reads reference_values.json. The Python analysis fixes every priority order before reading those values. Any returned likelihood ties within 1e-8 use the frozen value-blind project order; all eight actual fits returned one solution.

## Reproduce

Install R 4.5.2 and the official rankrate 1.2.1 source archive with its gtools and isotone dependencies. The recorded run used gtools 3.9.5, isotone 1.1-2 and nnls 1.6. The adjacent rankrate_source directory in the preview package contains the original source archive and its URL/hash record.

    Rscript fit_rankrate.R . direct FV
    Rscript fit_rankrate.R . direct Greedy
    Rscript fit_rankrate.R . direct GreedyLocal
    Rscript fit_rankrate.R . direct ASTAR

Repeat the commands with score_derived in place of direct to run the dependence check. Then run:

    python3 -B analyze_results.py

The outputs directory retains the original R fit objects, all returned orders, parameter estimates and joint log likelihoods. results.json and comparison.csv contain 17 selection procedures or checks at every funding capacity from one through nine. The reader preview verifies an evaluation fingerprint before using the saved R orders; it does not require R for portfolio recomputation.

## Capacity-three results

| Procedure | Selected applications | Total reference value | Selection loss |
| --- | --- | ---: | ---: |
| Mean score | P01, P05, P07 | 2.5250 | 0.1375 |
| Midpoint voting | P01, P05, P07 | 2.5250 | 0.1375 |
| Ranking derived from scores | P01, P05, P03 | 2.5375 | 0.1250 |
| Direct-ranking Borda | P07, P01, P03 | 2.6625 | 0.0000 |
| Joint FV, direct rankings | P07, P01, P03 | 2.6625 | 0.0000 |
| Joint Greedy / GreedyLocal / ASTAR, direct rankings | P01, P07, P03 | 2.6625 | 0.0000 |
| All four joint methods, score-derived rankings | P01, P05, P03 | 2.5375 | 0.1250 |

The main Individual baseline uses reviewer 2, as in the numerical appendix. E01, categorical recommendations and the inclusive 70-point threshold remain supplementary. Every row reports both total loss and loss per funded project.

For capacities two through nine, the four joint methods using direct rankings select the same sets as direct Borda. At capacity one, Greedy, GreedyLocal and ASTAR select reference value 0.9000; direct Borda and FV select 0.8750. This single-pool experiment demonstrates the completed workflow and supports comparing the methods on further pools. Corresponding-scholar validation remains planned.
