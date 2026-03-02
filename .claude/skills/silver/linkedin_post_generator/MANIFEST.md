# LinkedIn Post Generator — Manifest

**Created:** 2026-02-25
**Domain:** silver
**Status:** Production Ready
**Version:** 1.0.0

## Overview

Generates a professional LinkedIn post draft (≤200 words) from vault context. Saves to `/Social/LinkedIn_Draft_YYYY-MM-DD.md` with `requires_approval: true`. Never publishes automatically.

## Components

- `SKILL.md` — Full specification, schemas, tone guidelines, blueprints
- `README.md` — Quick start
- `MANIFEST.md` — This file
- `assets/linkedin_post_generator.py` — Python generator (~200 LOC)

## Integration Points

| Direction | Path |
|---|---|
| Reads | `Company_Handbook.md`, `Dashboard.md`, `/Done/*.md` |
| Writes draft | `/Social/LinkedIn_Draft_YYYY-MM-DD.md` |
| Writes log | `/Logs/linkedin-post-YYYY-MM-DD.log` |
| Upstream | Any workflow that wants a social post drafted |
| Downstream | Human reviews draft → publishes manually |
