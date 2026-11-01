# Review protocol and public prompt templates

The completed experiment used five publication-based agents and ten constructed research applications. Each agent evaluated each application in a separate request, giving 50 review tasks. A further request asked each agent to rank all ten applications, giving five ranking tasks. Agents worked independently and received no other agent's responses.

## Scoring and ranking

For a review task, the agent received one publication-based expert profile, one complete application, and the NSFC-informed review instrument. It rated novelty, scientific value, and foundations and feasibility on 1–5 scales, with a short application quotation and explanation for each rating. The response also recorded familiarity, overall grade, and a funding recommendation. These are three criteria for assessing the whole application, not separate disciplinary-component scores. The program calculated the numerical total and reverse-coded integer score from those ratings.

For the ranking task, the agent received the same profile and all ten applications. It did not receive the earlier scores, other agents' responses, or the project reference values. Application order was shuffled with seed `1028 + numeric reviewer identifier`. The agent submitted a complete funding-priority order. The separately submitted ranking and reverse-coded scores then entered the joint model.

Project component values, importance weights, reference values, coded contribution targets, and the optimal portfolio were withheld from both tasks. The scientific contributions described in the application remain visible because they are the content being evaluated.

## Files and model settings

`system.txt`, `scoring.txt`, and `ranking.txt` retain the actual instruction text used by the completed review protocol. Their wording was extracted from the experiment implementation. They contain no source publications or personal identities. `model_settings.json` records the requested model identifier `deepseek-v4-pro-0813`, temperature 0.3, maximum output length 2,300 tokens, JSON response format, and disabled thinking mode. The recorded run used a chat-completions-compatible endpoint. The model identifier and endpoint are provider-specific; new experiments should record the provider, available model identifier, returned model version, and complete settings. The public package does not contain an API endpoint, API key, or executable network client.

The archived agents received the original publication titles, abstracts, and per-paper keyword profiles. The public package releases anonymous derived profiles with research summaries, topic and method keywords, and distinct-paper frequencies. It does not redistribute the source-paper packets. Consequently, these public profiles can support new experiments, but the resulting prompts do not reproduce the archived requests token for token. The archived evaluation records and their original input hashes are preserved for provenance; public request hashes are labelled separately.

## Build and check anonymous requests

From the repository root, run:

```sh
python3 -B research/protocol/build_requests.py
```

This command constructs and checks 50 review requests and five ranking requests in memory. It makes no network requests. To save the public requests for a new experiment:

```sh
python3 -B research/protocol/build_requests.py --output /tmp/reviewlab-public-requests.jsonl
```

The builder explicitly selects the application text and anonymous profile fields. It excludes project-value metadata and rejects hidden researcher fields anywhere in the nested model packets. Its checks also verify that each scoring request contains one application and each ranking request contains the full pool without prior scores. Settings and instructions match the archived protocol, while the profile packet is the public-data adaptation described above.

The saved portfolio calculations and the R joint-model refits do not require new language-model calls. Refer to the repository README and `research/rankrate_alignment/README.md` for those reproduction steps. Corresponding-scholar verification and human–AI comparisons remain planned.
