---
name: planner
description: Create a detailed AI agent implementation plan document under the planner/ directory. Use this when you want to document an agentic AI use case with full workflow diagrams, code snippets, security considerations, and test cases before writing production code.
---

"""
1. Create an indexed markdown file like <index>_<use_case_name>.md under the planner/ directory.
2. The file MUST contain only one implementation use case scenario for agentic AI development.
3. The file MUST include all of the following sections:
   - "Use Case Description / Scenario"
   - "Objective"
   - "Recommended Approach" (chosen pattern, alternatives considered, justification)
   - "Security Considerations" (prompt injection, input validation, secrets management)
   - "Step-by-Step Thought Process"
   - "Pseudo Code"
   - "High Level Workflow Diagram"
   - "Low Level Workflow Diagram"
   - "Implementation Steps"
   - "Code Snippets"
   - "Test Cases"
   - "Expected Outcomes"
4. The file MUST include test case scenarios and instructions on how to execute them.
5. The use case SHOULD be practical and MUST demonstrate the capabilities of agentic AI in a real-world scenario.
6. Implementation steps MUST follow the conventions in .github/copilot-instructions.md (use common/ package, LCEL pipes, LangGraph for agents).
"""