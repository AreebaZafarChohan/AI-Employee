# Research: Platinum Tier Backend

**Feature**: Platinum Tier Backend Upgrade
**Date**: 2026-03-08

## Decision 1: Vector Database Selection
- **Decision**: Use `pgvector` with PostgreSQL.
- **Rationale**: 
    - Aligns with the **Simplicity (YAGNI)** principle in the constitution.
    - Leverages the existing PostgreSQL database, avoiding the operational overhead of managing a separate ChromaDB service.
    - Prisma has support for `pgvector` via raw queries or specific extensions, keeping the stack unified.
- **Alternatives considered**: 
    - **ChromaDB**: Rejected because it introduces a new service dependency and more complex deployment for a single-tenant system.
    - **Pinecone**: Rejected as it's a managed service and introduces external dependency and potential cost/privacy concerns.

## Decision 2: Autonomous Planning Strategy
- **Decision**: Hierarchical Task Decomposition using a dedicated `PlannerAgent`.
- **Rationale**: 
    - A single-shot decomposition can be brittle for complex goals.
    - A hierarchical approach allows the `PlannerAgent` to create high-level phases, which are then further decomposed by the `TaskAnalyzerAgent` as needed.
    - This separation of concerns (Planning vs. Execution Analysis) improves reliability.
- **Alternatives considered**: 
    - **Flat List Generation**: Rejected as it fails to handle inter-task dependencies and complex branching logic well.
    - **AutoGPT-style loops**: Rejected because they can easily get stuck in loops and exceed cost thresholds without human-in-the-loop (which our spec requires).

## Decision 3: MCP-Compatible Tool Interface
- **Decision**: Implement a shim layer that translates internal tool calls to the **Model Context Protocol (MCP)** specification.
- **Rationale**: 
    - Ensures future-proofing and interoperability with the growing ecosystem of MCP servers.
    - Allows the system to easily "plug in" new tools without refactoring the core orchestrator.
- **Alternatives considered**: 
    - **Proprietary JSON-RPC**: Rejected as it limits extensibility.

## Decision 4: Token Accounting & Cost Estimation
- **Decision**: Use `js-tiktoken` (or equivalent for specific models) for client-side estimation and persist usage from API responses.
- **Rationale**: 
    - Provides real-time feedback (SC-006) before the provider's billing cycle is updated.
    - Most LLM APIs (OpenAI, Anthropic) provide `usage` fields in their responses, which will be the "Source of Truth" for `CostLog`.
- **Alternatives considered**: 
    - **External monitoring tools (e.g., Helicone)**: Rejected to keep the system self-contained and avoid extra dependencies.

## Decision 5: Multi-Agent Collaboration Pattern
- **Decision**: Orchestrator-led delegation with a "Supervisor" gate.
- **Rationale**: 
    - The `SupervisorAgent` acts as a final quality and risk check before tool execution or plan finalization.
    - This matches the "Human-in-the-loop" requirement from the spec (approval before execution).
- **Alternatives considered**: 
    - **Peer-to-peer agent communication**: Rejected as it is harder to monitor, audit, and enforce safety limits.
