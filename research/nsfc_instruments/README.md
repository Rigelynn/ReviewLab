# NSFC review instrument

The experiment adapts the NSFC General Program review form for free-exploration research (`面上项目51.pdf`). The corresponding goal-oriented form (`面上项目53.pdf`) is included for reference. Both PDFs are original source instruments supplied for the study and have not been rewritten.

The form records familiarity, an overall grade, a funding recommendation and written assessments of the application. The field-and-rule JSON records the source categories and their relationships.

For the experimental task, we add 1–5 ratings of novelty, scientific value, and foundations and feasibility. A separate task asks for a complete funding-priority ranking of the project pool. These numerical ratings and rankings are research additions; they are not represented as requirements of the NSFC source form.

The actual prompts and recorded model settings appear in `../protocol/`. The technical appendix describes how the ratings are transformed into numerical totals and reverse-coded integer scores for joint estimation.
