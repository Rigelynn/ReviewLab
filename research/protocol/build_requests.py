"""Build anonymous review requests from the public materials; never calls an API."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

PROTOCOL = Path(__file__).resolve().parent
ROOT = PROTOCOL.parents[1]
FORBIDDEN_KEYS = {
    "x", "rho", "q", "alpha", "x_ik", "rho_ik", "q_i", "value_weights",
    "reference_value", "reference_values", "researcher_values", "true_value",
    "true_quality", "optimal_portfolio", "best_selected", "best_value",
    "knowledge_design", "contribution_targets", "contribution_target_codes",
    "supported_targets", "target_codes", "material_validation", "label_source",
    "label_agreement", "label_evidence", "disciplinary_breadth",
}


def read(name):
    return (PROTOCOL / name).read_text(encoding="utf-8").strip()


def assert_no_hidden_fields(value):
    """Check the full nested model packet, including substituted materials."""
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = key.casefold()
            if (normalized in FORBIDDEN_KEYS or normalized.startswith("researcher_")
                    or "contribution_target" in normalized or "optimal_portfolio" in normalized):
                raise ValueError("Hidden research field in model input: " + key)
            assert_no_hidden_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_no_hidden_fields(nested)


def application(project):
    # Explicit allowlists prevent benchmark metadata from entering any prompt.
    return {
        "id": project["id"], "title": project["title"],
        "duration_months": project["duration_months"], "budget_units": project["budget_units"],
        "sections": [{key: section[key] for key in ("id", "heading", "text")}
                     for section in project["sections"]],
    }


def profile(expert):
    # The public derived profile substitutes for the private source-paper packet.
    return {
        "expert_id": expert["id"], "cutoff": expert["cutoff"],
        "publication_count": expert["publication_count"],
        "knowledge_profile": {
            "summary_en": expert["knowledge_profile"]["summary_en"],
            "topic_keywords": [{key: row[key] for key in ("term", "paper_count")}
                               for row in expert["topic_keywords"]],
            "method_keywords": [{key: row[key] for key in ("term", "paper_count")}
                                for row in expert["method_keywords"]],
        },
    }


def model_parameters():
    settings = json.loads(read("model_settings.json"))
    return {key: settings[key] for key in (
        "model", "temperature", "max_tokens", "stream", "enable_thinking", "response_format")}


def instrument(materials):
    # Retain the actual rubric, not the researcher-facing project-value table.
    return deepcopy(materials["rubric"])


def requests(materials):
    if len(materials["experts"]) != 5 or len(materials["projects"]) != 10:
        raise ValueError("This development-pool protocol requires five profiles and ten applications")
    records = []
    for expert in materials["experts"]:
        for project in materials["projects"]:
            packet = {"experiment_notice": materials.get("experiment_notice", ""),
                      "expert_profile": profile(expert), "application": application(project),
                      "instrument": instrument(materials)}
            records.append(make_record(expert["id"], project["id"], "rubric", packet))
    for expert in materials["experts"]:
        projects = list(materials["projects"])
        random.Random(1028 + int(expert["id"][1:])).shuffle(projects)
        packet = {"experiment_notice": materials.get("experiment_notice", ""),
                  "expert_profile": profile(expert), "applications": [application(p) for p in projects],
                  "instrument": instrument(materials)}
        records.append(make_record(expert["id"], None, "ranking", packet))
    return records


def make_record(expert_id, project_id, task, packet):
    assert_no_hidden_fields(packet)
    prompt = read("scoring.txt" if task == "rubric" else "ranking.txt")
    body = model_parameters()
    body["messages"] = [
        {"role": "system", "content": read("system.txt")},
        {"role": "user", "content": json.dumps(packet, ensure_ascii=False) + "\nTASK: " + prompt},
    ]
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"id": f"{expert_id}_{project_id or 'all'}_{task}_public",
            "expert_id": expert_id, "project_id": project_id, "task": task,
            "public_input_sha256": digest, "request": body}


def validate(records):
    assert len(records) == 55
    reviews = [r for r in records if r["task"] == "rubric"]
    rankings = [r for r in records if r["task"] == "ranking"]
    assert len(reviews) == 50 and len(rankings) == 5
    assert len({(r["expert_id"], r["project_id"]) for r in reviews}) == 50
    for record in records:
        user = record["request"]["messages"][1]["content"]
        packet = json.loads(user.split("\nTASK: ", 1)[0])
        assert_no_hidden_fields(packet)
        assert "publications" not in packet["expert_profile"]
        if record["task"] == "rubric":
            assert "applications" not in packet
            assert packet["application"]["id"] == record["project_id"]
        else:
            assert len(packet["applications"]) == 10
            assert len({p["id"] for p in packet["applications"]}) == 10
            assert not any(key in packet for key in ("scores", "reviews", "prior_scores"))
    # The guard must reject hidden fields even when nested in a supplied section.
    for field in ["q", "x_ik", "rho_ik", "contribution_targets", "optimal_portfolio"]:
        try:
            assert_no_hidden_fields({"application": {"sections": [{field: 0.99}]}})
        except ValueError:
            pass
        else:
            raise AssertionError("Hidden-field check did not reject " + field)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materials", type=Path, default=ROOT / "data/nsfc_panel_v3/materials.json")
    parser.add_argument("--output", type=Path, help="Write public requests as JSONL; no model is called")
    args = parser.parse_args()
    materials = json.loads(args.materials.read_text(encoding="utf-8"))
    records = requests(materials)
    validate(records)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                               encoding="utf-8")
    print(json.dumps({"review_requests": 50, "ranking_requests": 5,
                      "hidden_field_checks": "passed", "network_requests": 0,
                      "output_written": bool(args.output)}))


if __name__ == "__main__":
    main()
