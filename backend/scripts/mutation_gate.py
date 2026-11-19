"""Calcula el Mutation Score de mutmut y hace fallar el build si es menor al umbral.

Uso:  python scripts/mutation_gate.py --min 50 [--badge badges/mutation.json]
"""
import argparse
import json
import sys
from pathlib import Path


def score(stats: dict) -> float:
    detectados = stats["killed"] + stats.get("timeout", 0)
    evaluados = stats["total"] - stats.get("skipped", 0)
    return 100.0 * detectados / evaluados if evaluados else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", default="mutants/mutmut-cicd-stats.json")
    ap.add_argument("--min", type=float, default=50.0)
    ap.add_argument("--badge", default=None)
    args = ap.parse_args()

    stats = json.loads(Path(args.stats).read_text())
    s = score(stats)
    print(f"Mutantes: {stats['total']} | muertos: {stats['killed']} | "
          f"sobrevivientes: {stats['survived']} | Mutation Score: {s:.1f}%")

    if args.badge:
        color = "brightgreen" if s >= 80 else "yellow" if s >= 60 else "red"
        Path(args.badge).parent.mkdir(parents=True, exist_ok=True)
        Path(args.badge).write_text(json.dumps(
            {"schemaVersion": 1, "label": "mutation score", "message": f"{s:.0f}%", "color": color}))

    if s < args.min:
        print(f"::error::Mutation Score {s:.1f}% por debajo del mínimo {args.min}%")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
