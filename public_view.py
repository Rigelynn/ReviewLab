"""Derived reader data, separate from frozen research and reviewer inputs."""
from collections import Counter
from copy import deepcopy
import math


def keyword_frequencies(papers, key):
    """Count distinct source papers per term, ignoring within-paper repeats."""
    counts = Counter()
    labels = {}
    for paper in papers:
        seen = set()
        for value in paper.get(key, []):
            if not isinstance(value, str):
                continue
            term = " ".join(value.split())
            normalized = term.casefold()
            if not term or normalized in seen:
                continue
            seen.add(normalized)
            labels.setdefault(normalized, term)
            counts[normalized] += 1
    # Counter preserves source order for ties; frequency is never a relevance score.
    return [{"term": labels[term], "paper_count": count}
            for term, count in counts.most_common()]


def rao_stirling(shares, delta):
    """Use the same ordered-pair sum and field geometry as project breadth D."""
    if not shares or any(not math.isfinite(v) or v < 0 for v in shares.values()):
        raise ValueError("Field shares must be finite and nonnegative")
    if not math.isclose(sum(shares.values()), 1.0, abs_tol=1e-6):
        raise ValueError("Field shares must sum to one")
    return sum(shares[k] * shares[l] * delta[k][l]
               for k in shares for l in shares)


def reader_materials(materials):
    """Project display data plus source-free, deterministically derived profiles."""
    result = {key: deepcopy(materials[key]) for key in
              ["version", "taxonomy", "projects", "rubric", "human_validation",
               "material_validation"] if key in materials}
    geometry = materials["geometry"]
    result["geometry"] = {key: deepcopy(geometry[key])
                          for key in ["source", "scope", "delta"] if key in geometry}
    result["experts"] = []
    derived = {profile["id"]: profile for profile in materials.get("derived_profiles", [])}
    for expert in materials["experts"]:
        source = derived.get(expert["id"], expert)
        profile = source["knowledge_profile"]
        papers = profile.get("papers")
        # Public releases can retain this derived view and calculation vectors
        # without redistributing the source publications used by the local study.
        if papers is not None:
            publication_count = len(papers)
            topics = keyword_frequencies(papers, "keywords")
            methods = keyword_frequencies(papers, "methods")
        else:
            publication_count = source["publication_count"]
            topics = deepcopy(source["topic_keywords"])
            methods = deepcopy(source["method_keywords"])
        result["experts"].append({
            "id": expert["id"],
            "cutoff": source["cutoff"],
            "publication_count": publication_count,
            "knowledge_profile": {"summary_en": profile.get("summary_en", "")},
            "field_shares": deepcopy(expert["field_shares"]),
            "topic_keywords": topics,
            "method_keywords": methods,
            "disciplinary_breadth": {
                "value": rao_stirling(expert["field_shares"], geometry["delta"]),
                "method": "Rao–Stirling",
                "definition": "sum_k,l f_jk * f_jl * Delta_kl",
                "geometry_source": geometry["source"],
                "scope": geometry["scope"],
            },
        })
    return result


def reader_status(status):
    """Keep review outputs and opaque provenance; omit prompts and raw packets."""
    result = {key: deepcopy(status[key]) for key in
              ["source", "version", "execution_mode", "human_validation",
               "material_validation"] if key in status}
    result["job"] = {key: deepcopy(status.get("job", {})[key]) for key in
                     ["status", "completed", "total", "actual", "failed"]
                     if key in status.get("job", {})}
    fields = ["id", "expert_id", "project_id", "task", "status", "parsed",
              "input_sha256", "model_requested", "response_model", "timestamp"]
    result["records"] = [{key: deepcopy(record[key]) for key in fields if key in record}
                         for record in status.get("records", [])]
    return result
