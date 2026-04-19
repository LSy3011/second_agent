---
name: interview-coach
description: Use when the agent needs to prepare AI application engineer interviews, generate likely questions, simulate follow-up questions, or build answer frameworks from user projects and target job requirements.
---

# Interview Coach

Use this workflow to prepare structured interview answers from user projects.

## Inputs

- Target position.
- User project memory.
- Resume bullets or project summaries.
- Known weak points or concerns.

## Workflow

1. Identify the interview focus: RAG, Agent, MCP, vector database, graph database, evaluation, deployment, or debugging.
2. Select the most relevant project facts from memory.
3. Generate likely questions and follow-up questions.
4. For each answer, use Background, Design, Tradeoff, Failure Handling, Result.
5. Mark which claims require server-side verification before the interview.

## Output

Return:

- 8 to 12 interview questions.
- Suggested answer outline for each question.
- 3 deeper follow-up chains.
- A final checklist of facts to verify.

