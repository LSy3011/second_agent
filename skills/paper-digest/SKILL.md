---
name: paper-digest
description: Use when the agent needs to summarize papers, compare methods, extract technical claims, connect papers to user projects, or call Paper Assistant/MCP tools for literature review.
---

# Paper Digest

Use this workflow to convert papers into reusable research notes.

## Inputs

- Paper title, PDF path, or research question.
- Optional Paper Assistant MCP tools: paper_search, paper_ask, graph_neighbors.
- User goal, such as project design, technical research, internal documentation, or literature review.

## Workflow

1. Clarify the research question.
2. Call Paper Assistant tools if available.
3. Extract problem, method, experiment setup, result, limitation, and reusable idea.
4. Compare related papers by method, metric, dataset, and engineering implication.
5. Connect the paper to the user's project, architecture decision, or technical research task.

## Output

Return:

- One paragraph summary.
- Method breakdown.
- Key claims and evidence.
- Limitations.
- Reusable project or architecture talking points.
