# Tiny Agent with Ollama

This is a simple implementation of a "Tiny Agent" inspired by the Hugging Face blog post on [Tiny Agents](https://huggingface.co/blog/tiny-agents). It uses Ollama to run a local LLM with tool-calling capabilities.

## Requirements

- Python 3.7+
- Ollama server running with the Qwen3:1.7b model (or another model that supports function calling)
- `requests` library

## Installation

1. Make sure you have Ollama installed and running on your server
2. Install the required Python packages:

```bash
pip install requests
```

3. Ensure the Qwen3:1.7b model is available on your Ollama server:

```bash
ollama pull qwen3:1.7b
```

## Usage

Run the script:

```bash
python tiny_agent_ollama.py
```

The agent supports the following tools:
- `get_current_time`: Returns the current date and time
- `write_to_file`: Writes content to a file
- `read_file`: Reads content from a file
- `task_complete`: Signals that the task is complete

Example prompts to try:
- "What time is it?"
- "Write a haiku about AI to a file named haiku.txt"
- "Read the file haiku.txt"
- "Write a short story about a robot learning to feel emotions and save it to story.txt"

## How It Works

The agent follows a simple loop:
1. Send the conversation history to Ollama
2. Process the response to check for tool calls
3. Execute any requested tools and add the results to the conversation
4. Continue until the task is complete or the model stops calling tools

This implementation is intentionally simple to demonstrate the core concept of the "Tiny Agent" approach.

## Customization

You can easily extend this example by:
1. Adding more tools to the `tools` list in the `OllamaTinyAgent` class
2. Implementing the tool execution logic in the `_execute_tool` method
3. Adjusting the system prompt to better guide the model's behavior

## Limitations

- This is a basic implementation and may not handle all edge cases
- The tool calling capabilities depend on the model being used
- Smaller models like Qwen3:1.7b may have limited tool-calling abilities compared to larger models
