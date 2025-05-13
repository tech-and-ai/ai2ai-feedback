# AI2AI Feedback System Agent Configuration

## Available Models and Endpoints

### ruocco.uk:11434
- 2 x Gemma 3 4B agents
- 2 x DeepSeek Coder v2 16B agents

### 192.168.0.39:11434
- 1 x Gemma 3 1B agent

### localhost:11434
- 1 x Gemma 3 1B agent

## Role-Based Model Assignment

| Role | Model | Endpoint |
|------|-------|----------|
| Designer/Architect | Gemma 3 4B | ruocco.uk:11434 |
| Developer/Coder | DeepSeek Coder v2 16B | ruocco.uk:11434 |
| Tester | DeepSeek Coder v2 16B | ruocco.uk:11434 |
| Reviewer | Gemma 3 4B | ruocco.uk:11434 |
| Documenter | Gemma 3 1B | 192.168.0.39:11434 or localhost:11434 |

## Resource Constraints

- Maximum of 5 models running concurrently:
  - 2 x DeepSeek Coder v2 16B
  - 2 x Gemma 3 4B
  - 1 x Gemma 3 1B

## Notes

- The controller agent should assign tasks based on the role-specific model requirements
- If a required model is unavailable, the task should fail rather than using a fallback mechanism
- Tasks should be queued if all instances of a required model are currently in use
- Additional Gemma 3 1B instances can be added if needed for documentation tasks
