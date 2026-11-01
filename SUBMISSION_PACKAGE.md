# Organization Science submission package

The [call for science](https://pubsonline.informs.org/pb-assets/filesorsc/CFP_AI-Enabled%20Frontiers%20in%20Organizational%20Science-1785685920943.pdf) requests a short proposal, a technical appendix and a research artifact for Stage 1. This repository provides the artifact and copies of the two documents.

| Requested material | File or entry point |
| --- | --- |
| Short proposal describing the scientific contribution, completed work, planned work and risks | [proposal.docx](proposal.docx) |
| Technical details needed to understand and evaluate the work | [appendix.docx](appendix.docx) |
| Prototype or proof of concept and Git repository | [Hosted simulator](http://106.54.30.90:3389/reviewlab/) and the source files in this repository |
| Materials for reproducing the proof of concept | Anonymous profiles and applications, saved scores and rankings, eight fitted objects, R fitting scripts, Python calculation code and tests |

## Suggested reading and verification order

1. Read the short proposal for the research question and intended contribution.
2. Open the simulator and inspect a scholar profile and a matched application pair.
3. Load the saved experiment to inspect the criterion scores and separately submitted rankings.
4. Change funding capacity in Portfolio Selection and compare selected reference value and loss.
5. Run the checks listed in README.md, then inspect the appendix and fitting files for the detailed design.

The package demonstrates the completed AI review and portfolio-selection workflow. The corresponding-scholar validation and extensions to additional project pools are described as planned work. Numerical benchmark results in the appendix are distinct from the saved application-based experiment; their original simulation script is not included here.
