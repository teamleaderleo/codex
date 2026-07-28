# Code-mode orphan-fix research

This directory contains two related bodies of work:

1. technical research around lost code-mode session handles and adjacent process-lifecycle failures;
2. a broader public `openai/codex` issue-quality study used to calibrate report quality and implementation value.

## Start here

- [`issues/README.md`](issues/README.md) — canonical issue-study index, coverage map, current boundaries and notification guidance.
- [`reviewer-research-brief.md`](reviewer-research-brief.md) — authoritative 20-issue review ruleset.
- [`related-issue-cluster.md`](related-issue-cluster.md) — failure-layer map around #35613.
- [`issue-implementation-value.md`](issue-implementation-value.md) — curated implementation-value calibration examples.

## Canonical issue-study storage

New work lives under [`issues/`](issues/), one file per exactly 20 unique issues. Legacy catalogue files remain in this directory as historical snapshots and are indexed from [`issues/README.md`](issues/README.md).

## Publication material

Public-facing issue, implementation and validation drafts live in the sibling [`../publication/`](../publication/) directory.

## Safety

No issue-study task should post upstream comments, reactions, labels, reviews or edits. Ordinary public issue links inside these committed Markdown notes do not notify issue participants, though the files remain public and discoverable.
