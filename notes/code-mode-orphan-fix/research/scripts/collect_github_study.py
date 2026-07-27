#!/usr/bin/env python3
"""Collect a reproducible public-issue sample from openai/codex.

The collector deliberately separates raw GitHub facts from provisional machine coding.
Human review is still required for the fixed quality rubric and nuanced comment coding.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

API_ROOT = "https://api.github.com"
SOURCE_REPO = "openai/codex"
MAINTAINER_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
AUTHORITY_EVENTS = {
    "assigned",
    "unassigned",
    "labeled",
    "unlabeled",
    "milestoned",
    "demilestoned",
    "locked",
    "unlocked",
    "transferred",
    "closed",
    "reopened",
}
INFO_REQUEST_RE = re.compile(
    r"\b(please|could you|can you|would you|provide|share|attach|reproduce|repro|"
    r"logs?|version|clarif|steps?|screenshot|diagnostic|feedback)\b|\?",
    re.IGNORECASE,
)
SUBSTANTIVE_RE = re.compile(
    r"\b(fix(?:ed|ing)?|diagnos(?:is|ed|tic)|root cause|workaround|implemented|"
    r"merged|landed|released|commit|pull request|\bpr\b|source|design|confirmed|"
    r"expected behavior|not supported|duplicate of|tracked in|resolved|regression)\b",
    re.IGNORECASE,
)


def parse_dt(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def fmt_dt(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def is_bot(user: dict[str, Any] | None) -> bool:
    if not user:
        return False
    login = str(user.get("login") or "")
    return user.get("type") == "Bot" or login.endswith("[bot]")


@dataclass
class GitHubClient:
    token: str
    user_agent: str = "teamleaderleo-codex-triage-study/1.0"
    search_delay_seconds: float = 2.1

    def _request(self, url: str, *, accept: str | None = None) -> tuple[Any, dict[str, str]]:
        headers = {
            "Accept": accept or "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self.user_agent,
        }
        request = urllib.request.Request(url, headers=headers)
        for attempt in range(8):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.load(response)
                    return payload, {k.lower(): v for k, v in response.headers.items()}
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                reset = exc.headers.get("X-RateLimit-Reset")
                remaining = exc.headers.get("X-RateLimit-Remaining")
                retry_after = exc.headers.get("Retry-After")
                if exc.code in {403, 429} and (remaining == "0" or retry_after or "rate limit" in body.lower()):
                    if retry_after:
                        sleep_for = max(1, int(retry_after))
                    elif reset:
                        sleep_for = max(1, int(reset) - int(time.time()) + 2)
                    else:
                        sleep_for = min(60, 2 ** attempt)
                    print(f"rate limited; sleeping {sleep_for}s", file=sys.stderr, flush=True)
                    time.sleep(sleep_for)
                    continue
                if exc.code >= 500 and attempt < 7:
                    time.sleep(min(30, 2 ** attempt))
                    continue
                raise RuntimeError(f"GitHub API {exc.code} for {url}: {body[:500]}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 7:
                    raise
                time.sleep(min(30, 2 ** attempt))
        raise RuntimeError(f"request retries exhausted: {url}")

    def get_paginated(self, path: str, params: dict[str, Any], *, search: bool = False) -> list[Any]:
        items: list[Any] = []
        page = 1
        while True:
            query = dict(params)
            query.update({"per_page": 100, "page": page})
            url = f"{API_ROOT}{path}?{urllib.parse.urlencode(query)}"
            if search:
                time.sleep(self.search_delay_seconds)
            payload, _headers = self._request(url)
            page_items = payload.get("items", []) if search else payload
            if not isinstance(page_items, list):
                raise RuntimeError(f"unexpected paginated response for {url}")
            items.extend(page_items)
            if len(page_items) < 100:
                break
            page += 1
            if search and page > 10:
                raise RuntimeError(f"search partition exceeded 1,000 retrievable results: {url}")
        return items

    def search_count(self, start: datetime, end: datetime) -> int:
        query = f"repo:{SOURCE_REPO} is:issue created:{fmt_dt(start)}..{fmt_dt(end)}"
        url = f"{API_ROOT}/search/issues?{urllib.parse.urlencode({'q': query, 'per_page': 1})}"
        time.sleep(self.search_delay_seconds)
        payload, _headers = self._request(url)
        return int(payload["total_count"])

    def search_interval(self, start: datetime, end: datetime) -> list[dict[str, Any]]:
        query = f"repo:{SOURCE_REPO} is:issue created:{fmt_dt(start)}..{fmt_dt(end)}"
        return self.get_paginated(
            "/search/issues",
            {"q": query, "sort": "created", "order": "asc"},
            search=True,
        )

    def comments(self, number: int) -> list[dict[str, Any]]:
        return self.get_paginated(f"/repos/{SOURCE_REPO}/issues/{number}/comments", {})

    def timeline(self, number: int) -> list[dict[str, Any]]:
        # Timeline preview is supported by the standard GitHub API media type.
        return self.get_paginated(f"/repos/{SOURCE_REPO}/issues/{number}/timeline", {})


def partitioned_search(client: GitHubClient, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Recursively partition until every GitHub Search slice is below 1,000 results."""
    frames: list[dict[str, Any]] = []

    def collect(lo: datetime, hi: datetime, depth: int = 0) -> None:
        count = client.search_count(lo, hi)
        print(f"partition {fmt_dt(lo)} .. {fmt_dt(hi)}: {count}", flush=True)
        if count <= 950:
            rows = client.search_interval(lo, hi)
            if len(rows) != count:
                raise RuntimeError(
                    f"partition count mismatch for {fmt_dt(lo)}..{fmt_dt(hi)}: "
                    f"expected {count}, retrieved {len(rows)}"
                )
            frames.extend(rows)
            return
        if depth > 20 or (hi - lo) <= timedelta(minutes=1):
            raise RuntimeError(f"cannot safely partition dense interval {lo}..{hi}")
        midpoint = lo + (hi - lo) / 2
        collect(lo, midpoint, depth + 1)
        # Avoid overlap at the exact midpoint because GitHub ranges are inclusive.
        collect(midpoint + timedelta(microseconds=1), hi, depth + 1)

    collect(start, end)
    deduped = {int(row["number"]): row for row in frames if "pull_request" not in row}
    result = [deduped[number] for number in sorted(deduped)]
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def compact_issue(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": int(row["number"]),
        "url": row.get("html_url"),
        "title": row.get("title") or "",
        "body": row.get("body") or "",
        "state": row.get("state"),
        "state_reason": row.get("state_reason"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "closed_at": row.get("closed_at"),
        "comments_count": row.get("comments", 0),
        "author_login": (row.get("user") or {}).get("login"),
        "author_type": (row.get("user") or {}).get("type"),
        "author_association": row.get("author_association"),
        "labels": [label.get("name") for label in row.get("labels", [])],
        "reactions_total": (row.get("reactions") or {}).get("total_count", 0),
    }


def sample_rows(rows: list[dict[str, Any]], size: int, seed: int) -> list[dict[str, Any]]:
    if len(rows) <= size:
        return list(rows)
    rng = random.Random(seed)
    chosen = set(rng.sample([int(row["number"]) for row in rows], size))
    return [row for row in rows if int(row["number"]) in chosen]


def authority_logins(issue: dict[str, Any], timeline: list[dict[str, Any]]) -> set[str]:
    author = issue.get("author_login")
    result: set[str] = set()
    for event in timeline:
        if event.get("event") not in AUTHORITY_EVENTS:
            continue
        actor = event.get("actor") or {}
        login = actor.get("login")
        if not login or is_bot(actor):
            continue
        if event.get("event") in {"closed", "reopened"} and login == author:
            continue
        result.add(login)
    return result


def is_verified_maintainer(comment: dict[str, Any], authority: set[str]) -> bool:
    user = comment.get("user") or {}
    if is_bot(user):
        return False
    if comment.get("author_association") in MAINTAINER_ASSOCIATIONS:
        return True
    return str(user.get("login") or "") in authority


def classify_maintainer_comment(body: str) -> str:
    text = body.strip()
    if SUBSTANTIVE_RE.search(text) or len(text) >= 320:
        return "substantive maintainer response"
    if INFO_REQUEST_RE.search(text):
        return "maintainer information request"
    return "maintainer acknowledgement"


def highest_engagement(
    issue: dict[str, Any],
    comments: list[dict[str, Any]],
    authority: set[str],
    cutoff: datetime,
) -> dict[str, Any]:
    author = issue.get("author_login")
    highest = "author-only/no external human response"
    level = 0
    flags = {
        "bot_response_present": False,
        "community_response_present": False,
        "maintainer_acknowledgement_present": False,
        "maintainer_information_request_present": False,
        "substantive_maintainer_response_present": False,
    }
    first_maintainer_at: datetime | None = None
    first_external_human_at: datetime | None = None
    for comment in comments:
        created_raw = comment.get("created_at")
        if not created_raw:
            continue
        created = parse_dt(created_raw)
        if created > cutoff:
            continue
        user = comment.get("user") or {}
        login = user.get("login")
        if is_bot(user):
            flags["bot_response_present"] = True
            continue
        if login == author:
            continue
        if first_external_human_at is None or created < first_external_human_at:
            first_external_human_at = created
        if is_verified_maintainer(comment, authority):
            if first_maintainer_at is None or created < first_maintainer_at:
                first_maintainer_at = created
            classification = classify_maintainer_comment(comment.get("body") or "")
            target_level = {
                "maintainer acknowledgement": 2,
                "maintainer information request": 3,
                "substantive maintainer response": 4,
            }[classification]
            if target_level > level:
                highest = classification
                level = target_level
            if classification == "maintainer acknowledgement":
                flags["maintainer_acknowledgement_present"] = True
            elif classification == "maintainer information request":
                flags["maintainer_information_request_present"] = True
            else:
                flags["substantive_maintainer_response_present"] = True
        else:
            flags["community_response_present"] = True
            if level < 1:
                highest = "unverified human/community response"
                level = 1
    return {
        "engagement": highest,
        "first_maintainer_at": fmt_dt(first_maintainer_at) if first_maintainer_at else None,
        "first_external_human_at": fmt_dt(first_external_human_at) if first_external_human_at else None,
        **flags,
    }


def linked_pr_numbers(timeline: list[dict[str, Any]]) -> list[int]:
    numbers: set[int] = set()
    for event in timeline:
        source = event.get("source") or {}
        issue = source.get("issue") or {}
        if issue.get("pull_request") and issue.get("number"):
            numbers.add(int(issue["number"]))
        subject = event.get("subject") or {}
        if subject.get("type") == "pull_request" and subject.get("url"):
            match = re.search(r"/pull/(\d+)", subject["url"])
            if match:
                numbers.add(int(match.group(1)))
    return sorted(numbers)


def outcome(issue: dict[str, Any], timeline: list[dict[str, Any]]) -> str:
    if issue.get("state") == "open":
        return "open unresolved"
    reason = issue.get("state_reason")
    if reason == "duplicate":
        return "duplicate"
    if reason == "not_planned":
        return "not planned"
    labels = {str(label).lower() for label in issue.get("labels", [])}
    if any("duplicate" in label for label in labels):
        return "duplicate"
    if any("expected" in label for label in labels):
        return "expected behaviour"
    if any("support" in label or "invalid" in label for label in labels):
        return "unsupported or support redirect"
    if linked_pr_numbers(timeline) or reason == "completed":
        return "completed/fixed"
    return "other closure"


def primary_type(issue: dict[str, Any]) -> str:
    labels = {str(label).lower() for label in issue.get("labels", [])}
    body = (issue.get("body") or "").lower()
    title = (issue.get("title") or "").lower()
    text = title + "\n" + body
    if any("security" in label or "privacy" in label for label in labels):
        return "security or privacy concern"
    if any("documentation" in label or label == "docs" for label in labels):
        return "documentation request"
    if any("question" in label or "support" in label for label in labels):
        return "support or usage question"
    if "enhancement" in labels or "feature request" in text or title.startswith("[rfc]"):
        return "feature request"
    if "model-behavior" in labels or "model behaviour" in text or "model behavior" in text:
        return "model-behaviour report"
    if "performance" in labels or any(term in text for term in ["performance", "memory leak", "disk", "cpu", "slow"]):
        return "performance or resource problem"
    if "bug" in labels:
        if any(term in text for term in ["intermittent", "sometimes", "occasionally", "sporadic", "flaky"]):
            return "intermittent bug"
        return "reproducible bug"
    if any(term in text for term in ["triage", "issue template", "contribution policy", "process issue"]):
        return "meta or process issue"
    return "unclear or mixed request"


def objective_features(issue: dict[str, Any]) -> dict[str, Any]:
    title = issue.get("title") or ""
    body = issue.get("body") or ""
    lower = body.lower()
    code_blocks = body.count("```") // 2
    links = len(re.findall(r"https?://", body))
    words = re.findall(r"\b\w+\b", body)
    has_actual_expected = (
        ("expected" in lower and any(token in lower for token in ["actual", "instead", "what issue are you seeing"]))
        or ("what is the expected behavior" in lower and "what issue are you seeing" in lower)
    )
    has_repro = any(token in lower for token in ["steps to reproduce", "steps can reproduce", "reproduction", "repro"])
    has_environment = any(token in lower for token in ["what version", "platform", "environment", "codex-cli", "codex app"])
    has_evidence = code_blocks > 0 or any(token in lower for token in ["log", "screenshot", "uploaded thread", "trace", "output:"])
    one_scope = not (len(re.findall(r"^#{2,4}\s+", body, flags=re.MULTILINE)) > 12 and len(words) > 1800)
    prior_art = bool(re.search(r"(?:#\d+|github\.com/openai/codex/issues/\d+)", body))
    diagnosis_disciplined = not bool(re.search(r"\b(definitely|obviously|clearly) caused by\b", lower))
    first_screen = len(words) <= 1200 and len(title.strip()) >= 12
    return {
        "body_word_count": len(words),
        "code_block_count": code_blocks,
        "external_link_count": links,
        "template_usage": "### what version" in lower or "### what issue are you seeing" in lower,
        "has_proposed_fix_or_source_analysis": any(token in lower for token in ["possible implementation", "proposed fix", "source", "implementation direction"]),
        "has_fork_or_prototype": any(token in lower for token in ["fork", "prototype", "commit/"]176),
        "machine_title_specificity": 2 if len(title) >= 25 and not re.fullmatch(r"(?i)(bug|issue|help|codex issue|not working)", title.strip()) else (1 if len(title) >= 12 else 0),
        "machine_user_impact": 2 if any(token in lower for token in ["impact", "blocked", "cannot", "fails", "risk", "data loss", "disk"]) else (1 if len(words) >= 80 else 0),
        "machine_actual_expected": 2 if has_actual_expected else (1 if "expected" in lower else 0),
        "machine_reproduction": 2 if has_repro and (code_blocks > 0 or re.search(r"\n\s*1\.", body)) else (1 if has_repro else 0),
        "machine_environment": 2 if has_environment and any(char.isdigit() for char in body) else (1 if has_environment else 0),
        "machine_evidence": 2 if has_evidence and (code_blocks > 0 or "uploaded thread" in lower) else (1 if has_evidence else 0),
        "machine_scope": 2 if one_scope and len(words) <= 1500 else (1 if one_scope else 0),
        "machine_prior_art": 2 if prior_art else None,
        "machine_diagnosis_discipline": 2 if diagnosis_disciplined else 0,
        "machine_first_screen_readability": 2 if first_screen and len(words) >= 30 else (1 if len(words) < 1800 else 0),
    }


def machine_quality_score(features: dict[str, Any]) -> float | None:
    keys = [key for key in features if key.startswith("machine_") and key not in {"machine_quality_score"}]
    values = [features[key] for key in keys if isinstance(features[key], int)]
    if not values:
        return None
    return sum(values) / (2 * len(values))


def enrich_sample(
    client: GitHubClient,
    sample: list[dict[str, Any]],
    snapshot: datetime,
    output_dir: Path,
    cohort_name: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    raw_threads: list[dict[str, Any]] = []
    for index, raw in enumerate(sample, start=1):
        issue = compact_issue(raw)
        number = issue["number"]
        print(f"{cohort_name}: fetching thread {index}/{len(sample)} #{number}", flush=True)
        comments = client.comments(number)
        timeline = client.timeline(number)
        authority = authority_logins(issue, timeline)
        created = parse_dt(issue["created_at"])
        day30 = created + timedelta(days=30)
        engagement_30 = highest_engagement(issue, comments, authority, min(day30, snapshot))
        engagement_t = highest_engagement(issue, comments, authority, snapshot)
        first_maintainer_at = engagement_t["first_maintainer_at"]
        first_maintainer_hours = None
        if first_maintainer_at:
            first_maintainer_hours = round((parse_dt(first_maintainer_at) - created).total_seconds() / 3600, 3)
        features = objective_features(issue)
        features["machine_quality_score"] = machine_quality_score(features)
        record = {
            **issue,
            "primary_issue_type_machine": primary_type(issue),
            "outcome_as_of_t_machine": outcome(issue, timeline),
            "verified_authority_logins": ";".join(sorted(authority)),
            "linked_pr_numbers": ";".join(str(value) for value in linked_pr_numbers(timeline)),
            "engagement_30d_machine": engagement_30["engagement"],
            "engagement_as_of_t_machine": engagement_t["engagement"],
            "first_verified_maintainer_at": first_maintainer_at,
            "first_verified_maintainer_hours": first_maintainer_hours,
            "late_maintainer_response": bool(first_maintainer_hours is not None and first_maintainer_hours > 720),
            **{f"30d_{key}": value for key, value in engagement_30.items() if key not in {"engagement", "first_maintainer_at", "first_external_human_at"}},
            **features,
            "coding_status": "machine provisional; requires rubric review",
        }
        records.append(record)
        raw_threads.append({"issue": issue, "comments": comments, "timeline": timeline})
    write_jsonl(output_dir / f"{cohort_name}-threads.jsonl", raw_threads)
    write_csv(output_dir / f"{cohort_name}-coded-machine.csv", records)
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n": len(records),
        "engagement_30d": Counter(row["engagement_30d_machine"] for row in records),
        "engagement_as_of_t": Counter(row["engagement_as_of_t_machine"] for row in records),
        "outcome_as_of_t": Counter(row["outcome_as_of_t_machine"] for row in records),
        "primary_issue_type_machine": Counter(row["primary_issue_type_machine"] for row in records),
        "bot_response_30d": sum(bool(row.get("30d_bot_response_present")) for row in records),
        "verified_maintainer_within_30d": sum(row["engagement_30d_machine"].startswith("maintainer") or row["engagement_30d_machine"].startswith("substantive") for row in records),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, help="Exact UTC ISO-8601 snapshot")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mature-size", type=int, default=300)
    parser.add_argument("--freshness-size", type=int, default=50)
    parser.add_argument("--mature-seed", type=int, default=3561301)
    parser.add_argument("--freshness-seed", type=int, default=3561302)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")
    snapshot = parse_dt(args.snapshot)
    mature_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    mature_end = snapshot - timedelta(days=30)
    freshness_start = mature_end + timedelta(microseconds=1)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "source_repository": SOURCE_REPO,
        "snapshot_t": fmt_dt(snapshot),
        "mature_start": fmt_dt(mature_start),
        "mature_end": fmt_dt(mature_end),
        "freshness_start": fmt_dt(freshness_start),
        "freshness_end": fmt_dt(snapshot),
        "mature_sample_size": args.mature_size,
        "freshness_sample_size": args.freshness_size,
        "mature_seed": args.mature_seed,
        "freshness_seed": args.freshness_seed,
        "sampling": "simple random sample without replacement from complete deduplicated date-partitioned frame",
        "coding": "objective fields plus provisional deterministic machine coding; human rubric review required",
    }
    write_json(output_dir / "study-config.json", config)

    client = GitHubClient(token=token)
    mature_frame_raw = partitioned_search(client, mature_start, mature_end)
    freshness_frame_raw = partitioned_search(client, freshness_start, snapshot)
    mature_frame = [compact_issue(row) for row in mature_frame_raw]
    freshness_frame = [compact_issue(row) for row in freshness_frame_raw]
    write_jsonl(output_dir / "mature-frame.jsonl", mature_frame)
    write_csv(output_dir / "mature-frame.csv", mature_frame)
    write_jsonl(output_dir / "freshness-frame.jsonl", freshness_frame)
    write_csv(output_dir / "freshness-frame.csv", freshness_frame)

    mature_sample_raw = sample_rows(mature_frame_raw, args.mature_size, args.mature_seed)
    freshness_sample_raw = sample_rows(freshness_frame_raw, args.freshness_size, args.freshness_seed)
    write_csv(output_dir / "mature-sample.csv", [compact_issue(row) for row in mature_sample_raw])
    write_csv(output_dir / "freshness-sample.csv", [compact_issue(row) for row in freshness_sample_raw])

    mature_records = enrich_sample(client, mature_sample_raw, snapshot, output_dir, "mature")
    freshness_records = enrich_sample(client, freshness_sample_raw, snapshot, output_dir, "freshness")
    summary = {
        "config": config,
        "frame_sizes": {"mature": len(mature_frame), "freshness": len(freshness_frame)},
        "mature": summarize(mature_records),
        "freshness": summarize(freshness_records),
        "limitations": [
            "Comment subtype, primary issue type, outcome detail, and quality fields marked machine are provisional rule-based coding.",
            "Timeline availability varies; unavailable event data must not be treated as proof that no triage action occurred.",
            "Human rubric scoring and reliability review are required before publication-quality claims about issue quality.",
        ],
    }
    write_json(output_dir / "machine-summary.json", summary)
    print(json.dumps(summary, indent=2, default=dict), flush=True)


if __name__ == "__main__":
    main()
