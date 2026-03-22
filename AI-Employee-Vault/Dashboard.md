# AI Employee Dashboard

## System Status
- **Watchers:** Not Running
- **Claude Status:** Idle
- **Pending Items:** 0

## Needs Action
```dataview
LIST FROM "Needs_Action"
SORT file.name ASC
```

> If no items appear, the queue is empty.

## Recent Completed Tasks
```dataview
TABLE file.mtime AS "Completed"
FROM "Done"
SORT file.mtime DESC
LIMIT 5
```

> Shows the 5 most recently completed items.

## Daily Briefings

- [[2026-02-25_Daily.md]]

## Weekly Briefings
- [[2026-03-08_Monday_Briefing.md]]

## Quick Links
- [[Company_Handbook]]
- [[Inbox/]]
- [[Needs_Action/]]
- [[Plans/]]
- [[Done/]]
- [[Logs/]]
