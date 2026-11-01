"""Compare frozen reviews using the numerical benchmark's selection procedures.

Run after fit_rankrate.R has produced all eight fits. This analysis does not call
an LLM. It fixes all priority orders before reading reference_values.json.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
METHODS = ["FV", "Greedy", "GreedyLocal", "ASTAR"]


def csv_rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def fitting_signature(projects, reviewers, scores, rankings):
    packet = {"projects": projects, "reviewers": reviewers, "M": 12,
              "scores": [[scores[e][p] for p in projects] for e in reviewers],
              "rankings": [rankings[e] for e in reviewers]}
    return hashlib.sha256(json.dumps(packet, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def calculate(root=ROOT):
    manifest = json.loads((root / "inputs/manifest.json").read_text())
    projects, reviewers = manifest["projects"], manifest["reviewers"]
    tie = {p: i for i, p in enumerate(manifest["tie_order"])}
    scores = {r["reviewer"]: {p: int(r[p]) for p in projects}
              for r in csv_rows(root / "inputs/scores_reverse.csv")}
    rankings = {}
    for scenario in ["direct", "score_derived"]:
        rankings[scenario] = {
            r["reviewer"]: [projects[int(r[f"position_{i}"]) - 1]
                            for i in range(1, len(projects) + 1)]
            for r in csv_rows(root / f"inputs/rankings_{scenario}.csv")}
    matching = json.loads((root / "inputs/matching_and_recommendations.json").read_text())
    sort = lambda utility: sorted(projects, key=lambda p: (-round(utility[p], 10), tie[p]))
    totals = {e: {p: 100 * (1 - scores[e][p] / 12) for p in projects} for e in reviewers}

    def cosine(a, b):
        return math.fsum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b)) / (
            math.sqrt(math.fsum(x*x for x in a.values())) *
            math.sqrt(math.fsum(x*x for x in b.values())))

    delegated = {p: max(reviewers, key=lambda e: cosine(matching["reviewer_fields"][e],
                                                       matching["project_fields"][p]))
                 for p in projects}
    utilities = {
        "Mean score": {p: math.fsum(totals[e][p] for e in reviewers)/len(reviewers) for p in projects},
        "Voting (midpoint threshold)": {p: sum(scores[e][p] < 6 for e in reviewers) for p in projects},
        "Ranking (from scores)": {p: sum(len(projects)-1-rankings["score_derived"][e].index(p)
                                           for e in reviewers) for p in projects},
        "Borda ranking": {p: sum(len(projects)-1-rankings["direct"][e].index(p)
                                   for e in reviewers) for p in projects},
        "Expertise-based delegation": {p: totals[delegated[p]][p] for p in projects},
        "Individual (E02)": totals[reviewers[1]],
        "Single reviewer E01 (supplementary)": totals[reviewers[0]],
        "Categorical vote (supplementary)": {
            p: sum(matching["recommendations"][e][p] != "do_not_fund" for e in reviewers)
            for p in projects},
        "Score-threshold vote (supplementary)": {
            p: sum(totals[e][p] >= 70 for e in reviewers) for p in projects},
    }
    orders = {name: sort(u) for name, u in utilities.items()}
    fits = {}
    for scenario in ["direct", "score_derived"]:
        fits[scenario] = {}
        for method in METHODS:
            folder = root / "outputs" / scenario / method
            status = csv_rows(folder / "status.csv")[0]
            if status["status"] != "completed":
                fits[scenario][method] = {"status": "error", "error": status.get("error")}
                continue
            summary = csv_rows(folder / "summary.csv")
            returned = csv_rows(folder / "orders.csv")
            params = csv_rows(folder / "parameters.csv")
            solutions = []
            for row, stats in zip(returned, summary):
                solution = int(row["solution"])
                order = [projects[int(row[f"position_{i}"])-1] for i in range(1, len(projects)+1)]
                solutions.append({"solution": solution, "order": order,
                                  "p": {p["project"]: float(p["p"]) for p in params
                                        if int(p["solution"]) == solution},
                                  "theta": float(stats["theta"]),
                                  "log_likelihood": float(stats["log_likelihood"])})
            maximum = max(s["log_likelihood"] for s in solutions)
            eligible = [s for s in solutions if maximum-s["log_likelihood"] <= 1e-8]
            chosen = min(eligible, key=lambda s: tuple(tie[p] for p in s["order"]))
            entry = {"status": "completed", "method": method, "version": "1.2.1",
                     "scenario": scenario, "order": chosen["order"],
                     "selected_solution": chosen["solution"], "solutions": solutions,
                     "elapsed_seconds": float(summary[0]["elapsed_seconds"]),
                     "nodes": int(float(summary[0]["nodes"]))}
            fits[scenario][method] = entry
            name = f"Joint MB · {method}" + (" (score-derived ranking)" if scenario != "direct" else "")
            orders[name] = chosen["order"]

    # Project values enter only after every baseline and fitted order is fixed.
    values = {p["project_id"]: p["q"] for p in json.loads(
        (root / "reference_values.json").read_text())["projects"]}
    oracle = sorted(projects, key=lambda p: (-values[p], tie[p]))
    comparisons = []
    for capacity in range(1, len(projects)):
        best = oracle[:capacity]
        best_value = math.fsum(values[p] for p in best)
        for name, order in orders.items():
            selected = order[:capacity]
            value = math.fsum(values[p] for p in selected)
            loss = best_value-value
            comparisons.append({"budget": capacity, "rule": name, "order": order,
                                "selected": selected, "value": round(value, 10),
                                "loss": round(loss, 10), "loss_per_project": loss/capacity,
                                "hit_rate": len(set(selected)&set(best))/capacity,
                                "oracle_value": best_value})
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and
             p.name not in {"results.json", "comparison.csv", "README.md"}]
    return {"analysis": "GenAI evaluations refitted with rankrate 1.2.1",
            "new_ai_calls": 0, "M": 12, "N": len(projects), "J": len(reviewers),
            "fitting_signature": fitting_signature(projects, reviewers, scores, rankings["direct"]),
            "tie_policy": "Maximum observed log likelihood; ties within 1e-8 use frozen value-blind order",
            "tie_order": manifest["tie_order"], "fits": fits, "comparisons": comparisons,
            "files_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in files}}


if __name__ == "__main__":
    result = calculate()
    (ROOT / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n")
    with (ROOT / "comparison.csv").open("w") as stream:
        fields = ["budget", "rule", "selected", "value", "loss", "loss_per_project", "hit_rate"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in result["comparisons"]:
            writer.writerow({**{k: row[k] for k in fields}, "selected": ";".join(row["selected"])})
    for row in result["comparisons"]:
        if row["budget"] == 3:
            print(row["rule"], row["selected"], row["value"], row["loss"])
