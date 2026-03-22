# Business Domain

This folder contains business operations items including clients, projects, and operations.

## Folder Structure

```
Business/
├── Clients/
│   ├── active/          # Active clients
│   ├── prospects/       # Potential clients
│   └── archive/         # Past clients
├── Projects/
│   ├── active/          # Currently active projects
│   ├── completed/       # Completed projects
│   └── backlog/         # Future projects
└── Operations/
    ├── hr/              # HR-related items
    ├── finance/         # Finance operations
    └── admin/           # Administrative tasks
```

## Domain Classification

Business domain includes:

| Category | Description | Examples |
|----------|-------------|----------|
| **Clients** | Client management | Active, prospects, past |
| **Projects** | Project management | Active, completed, backlog |
| **Operations** | Business operations | HR, finance, admin |

## Client Management

### Active Clients
Current clients with ongoing work or retainer agreements.

### Prospects
Potential clients being nurtured for future business.

### Archive
Past clients for reference and potential re-engagement.

## Project Management

### Active Projects
Currently executing projects with deadlines and deliverables.

### Completed Projects
Finished projects for portfolio and reference.

### Backlog
Future projects waiting for resources or timing.

## Operations

### HR
- Hiring processes
- Employee onboarding
- Training materials

### Finance
- Budget planning
- Financial operations
- Compliance

### Admin
- Office management
- Vendor relationships
- Legal matters

## Related Skills

- `domain_classifier` - Classifies tasks as business domain
- `task_prioritizer` - Prioritizes business tasks
- `project_tracker` - Tracks project progress
