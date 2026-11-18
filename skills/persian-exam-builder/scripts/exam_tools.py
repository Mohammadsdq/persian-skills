#!/usr/bin/env python3
"""Helpers for exams written as JSON (stdlib only).

  python exam_tools.py gift questions.json > quiz.gift     # Moodle "GIFT" import file
  python exam_tools.py balance questions.json              # is the answer key evenly spread?
  python exam_tools.py check questions.json                # structural problems in the question bank

questions.json is a list of objects:
  {"type": "mcq", "question": "...", "options": ["...", "...", "...", "..."], "answer": 2,
   "title": "optional", "feedback": "optional", "topic": "optional", "level": "optional"}
  {"type": "tf",    "question": "...", "answer": true}
  {"type": "short", "question": "...", "answer": ["accepted answer", "another accepted answer"]}
For mcq, "answer" is the 0-based index of the correct option (or its letter: "A", "B", ...).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

LETTERS = "ABCDEFGH"
SPECIAL = "~=#{}:"  # characters GIFT treats as syntax


def esc(text: str) -> str:
    out = []
    for ch in str(text).replace("\r", ""):
        out.append("\\" + ch if ch in SPECIAL else ch)
    return "".join(out).replace("\n", "\\n")


def answer_index(q: dict) -> int:
    a = q["answer"]
    if isinstance(a, str) and a.strip().upper() in LETTERS:
        return LETTERS.index(a.strip().upper())
    return int(a)


def validate(questions: list) -> list:
    problems = []
    for n, q in enumerate(questions, 1):
        where = f"question {n}"
        kind = q.get("type", "mcq")
        if not str(q.get("question", "")).strip():
            problems.append(f"{where}: empty question text")
        if kind == "mcq":
            opts = q.get("options") or []
            if len(opts) < 2:
                problems.append(f"{where}: needs at least 2 options")
                continue
            try:
                idx = answer_index(q)
                if not 0 <= idx < len(opts):
                    problems.append(f"{where}: answer index {idx} is outside the options")
            except (KeyError, ValueError, TypeError):
                problems.append(f"{where}: missing or invalid answer")
            stripped = [str(o).strip() for o in opts]
            if len(set(stripped)) != len(stripped):
                problems.append(f"{where}: two options are identical")
            if any(not o for o in stripped):
                problems.append(f"{where}: an option is empty")
            lowered = " ".join(stripped)
            if "همه‌ی موارد" in lowered or "همه موارد" in lowered or "هیچ‌کدام" in lowered or "هیچکدام" in lowered:
                problems.append(f"{where}: avoid 'all/none of the above' options")
        elif kind == "tf":
            if not isinstance(q.get("answer"), bool):
                problems.append(f"{where}: tf answer must be true or false")
        elif kind == "short":
            ans = q.get("answer")
            if not (isinstance(ans, str) or (isinstance(ans, list) and ans and all(isinstance(a, str) for a in ans))):
                problems.append(f"{where}: short answer needs a string or a list of strings")
        else:
            problems.append(f"{where}: unknown type {kind!r}")
    return problems


def to_gift(questions: list) -> str:
    blocks = []
    for n, q in enumerate(questions, 1):
        kind = q.get("type", "mcq")
        title = q.get("title") or f"Q{n:02d}"
        head = f"::{esc(title)}::{esc(q['question'])}"
        feedback = f"#{esc(q['feedback'])}" if q.get("feedback") else ""
        if kind == "mcq":
            idx = answer_index(q)
            lines = [f"={esc(o)}" if i == idx else f"~{esc(o)}" for i, o in enumerate(q["options"])]
            body = "\n".join(lines) + (f"\n{feedback}" if feedback else "")
            blocks.append(f"{head}{{\n{body}\n}}")
        elif kind == "tf":
            blocks.append(f"{head}{{{'TRUE' if q['answer'] else 'FALSE'}{feedback}}}")
        elif kind == "short":
            answers = q["answer"] if isinstance(q["answer"], list) else [q["answer"]]
            body = "\n".join(f"={esc(a)}" for a in answers)
            blocks.append(f"{head}{{\n{body}\n}}")
        else:
            raise ValueError(f"unknown question type {kind!r}")
    return "\n\n".join(blocks) + "\n"


def balance(questions: list) -> dict:
    counts = Counter()
    mcq = 0
    for q in questions:
        if q.get("type", "mcq") == "mcq":
            mcq += 1
            counts[LETTERS[answer_index(q)]] += 1
    return {"mcq": mcq, "counts": dict(sorted(counts.items()))}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Exam helpers")
    p.add_argument("command", choices=["gift", "balance", "check"])
    p.add_argument("path")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with open(args.path, encoding="utf-8") as f:
        questions = json.load(f)
    if not isinstance(questions, list):
        print("error: the JSON file must contain a list of questions", file=sys.stderr)
        return 2

    problems = validate(questions)
    if args.command == "check":
        for line in problems:
            print(line)
        print(f"{len(questions)} questions, {len(problems)} problem(s)")
        return 1 if problems else 0
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    if args.command == "gift":
        sys.stdout.write(to_gift(questions))
    else:
        info = balance(questions)
        total = info["mcq"]
        print(f"{total} multiple-choice questions")
        for letter, n in info["counts"].items():
            print(f"  {letter}: {n:>3}  ({n / total:.0%})")
        if total >= 8 and info["counts"]:
            share = max(info["counts"].values()) / total
            if share > 0.4 or len(info["counts"]) < min(4, len(LETTERS)):
                print("warning: the correct answers are not spread evenly; shuffle the options", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
