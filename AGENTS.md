# Coding & Exploration Rules: Graphify and Graft

## Rule: Always Use Graft and Graphify

1. **Graft MCP Integration**:
   - For codebase exploration, symbol lookups, call hierarchy tracing, and architectural inspection, always prefer **Graft** tools over manual file reading or regex search:
     - `graft_find_code`: Look up how functions/classes work or locate definitions.
     - `graft_find_all`: Find all occurrences of symbols across the workspace.
     - `graft_trace_calls`: Trace call graphs, callers, callees, and change impact.
     - `graft_file_api`: Inspect high-level file APIs and exports efficiently.
     - `graft_repo_map`: Explore the codebase map and organization.

2. **Graphify Knowledge Graph**:
   - For codebase architecture questions, dependency relationships, and holistic structure understanding, use **Graphify** (`graphify` skill and `graphify-out/` artifacts).
   - Treat queries about architecture, module boundaries, and relationships as Graphify queries first.
   - Maintain the knowledge graph for the project when significant structural changes occur.
