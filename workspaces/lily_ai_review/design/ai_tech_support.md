# AI Tech Support Guide: Using the AI Debugging Assistant

## Overview

This guide explains how to use the AI Debugging Assistant script (`ai_debug.sh`) to provide technical support, particularly for Stripe integration questions. The script connects to powerful AI models through OpenRouter and maintains conversation context, allowing for in-depth technical assistance.

## For AI Assistants

As an AI assistant, you can use this guide to understand how to direct users to utilize the debugging script effectively. The script provides a way for users to get technical help with programming issues, particularly related to Stripe integration.

## Script Capabilities

The AI Debugging Assistant can:

1. Connect to various AI models (Gemini, Claude, GPT-4, etc.) via OpenRouter
2. Maintain conversation context for follow-up questions
3. Save, load, and manage conversation histories
4. Export conversations to Markdown for documentation
5. Track token usage for cost management
6. Highlight code snippets for better readability
7. Customize system messages for specific domains (e.g., Stripe expertise)

## Setup Instructions

Direct users to set up the script with these steps:

```bash
# Download the script
curl -o ai_debug.sh https://raw.githubusercontent.com/username/repo/main/ai_debug_v2.sh
# Make it executable
chmod +x ai_debug.sh
# Install required dependency
sudo apt install jq
# Source the script
source ai_debug.sh
```

## API Key Configuration

The script requires an OpenRouter API key. Instruct users to:

```bash
# Set API key via environment variable
export OPENROUTER_API_KEY="sk-or-v1-your-api-key"

# OR use the built-in function
save_api_key "sk-or-v1-your-api-key"
```

## Basic Usage

Teach users these fundamental commands:

```bash
# Ask a question
call_ai_support "How do I implement Stripe webhooks in Node.js?"

# Reset conversation with a custom system message for Stripe expertise
reset_ai_conversation "You are a Stripe API expert. Provide detailed, technical answers with code examples when appropriate."

# View available commands
show_help
```

## Stripe Integration Support

For Stripe-specific support, recommend these approaches:

1. **Set a Stripe-focused system message**:
   ```bash
   reset_ai_conversation "You are a Stripe API expert. Provide detailed, technical answers about Stripe API integration, webhooks, payment processing, subscriptions, and error handling. Include code examples in relevant programming languages when appropriate."
   ```

2. **Ask specific Stripe questions**:
   ```bash
   call_ai_support "How do I handle Stripe webhook events securely in Python?"
   call_ai_support "What's the best way to implement subscription billing with Stripe?"
   call_ai_support "How do I debug a 'No such customer' error in Stripe?"
   ```

3. **Request code examples**:
   ```bash
   call_ai_support "Give me a complete example of creating a Stripe subscription with a trial period in Node.js"
   ```

## Managing Conversations

Explain how to manage conversation history:

```bash
# Save the current conversation
save_conversation "stripe_webhook_implementation.json"

# List all saved conversations
list_conversations

# Load a previous conversation
load_conversation "stripe_webhook_implementation.json"

# View a saved conversation
view_conversation "stripe_webhook_implementation.json"

# Export a conversation to Markdown
export_conversation_to_markdown "stripe_webhook_implementation.json"
```

## Model Selection

Different questions may benefit from different models:

```bash
# For complex Stripe architecture questions
change_model "anthropic/claude-3-opus-20240229"

# For quick Stripe API reference questions
change_model "google/gemini-2.5-flash-preview"

# For detailed Stripe implementation guidance
change_model "google/gemini-2.5-pro-preview"

# For comprehensive Stripe troubleshooting
change_model "openai/gpt-4o"
```

## Token Usage Tracking

For cost-conscious users:

```bash
# View token usage statistics
show_token_usage
```

## Troubleshooting Guide

Common issues and solutions:

1. **Connection errors**:
   - Check internet connection
   - Verify API key is valid
   - The script has retry logic built in

2. **Model availability**:
   - If a model is unavailable, try another model
   - Some models may have higher latency

3. **JSON parsing errors**:
   - Ensure jq is installed correctly
   - Try resetting the conversation

4. **Incomplete responses**:
   - Some very long responses might be truncated
   - Try breaking complex questions into smaller parts

## Example Workflow for Stripe Support

Here's a complete workflow example for helping with Stripe:

```bash
# Start with a Stripe-focused system message
reset_ai_conversation "You are a Stripe API expert focusing on subscription implementations."

# Ask initial question
call_ai_support "How do I implement a subscription with a free trial in Stripe?"

# Follow up with more specific questions
call_ai_support "How would I handle the trial expiration in Node.js?"

# Save the conversation for future reference
save_conversation "stripe_subscription_trial.json"

# Export to Markdown for documentation
export_conversation_to_markdown "stripe_subscription_trial.json"
```

## Best Practices for AI Assistants

When directing users to this tool:

1. **Suggest specific questions**: Help users formulate clear, specific technical questions.

2. **Recommend appropriate models**: Suggest models based on question complexity.

3. **Encourage conversation saving**: Remind users to save important conversations.

4. **Promote documentation export**: Suggest exporting conversations for team sharing.

5. **Highlight context maintenance**: Emphasize that follow-up questions maintain context.

## Stripe-Specific Question Templates

Provide these templates for common Stripe scenarios:

1. **Implementation questions**:
   ```
   "How do I implement [specific Stripe feature] in [programming language]?"
   ```

2. **Error troubleshooting**:
   ```
   "I'm getting a '[exact error message]' when trying to [action] in Stripe. How do I fix this?"
   ```

3. **Best practices**:
   ```
   "What are the best practices for handling [specific scenario] with Stripe?"
   ```

4. **Security concerns**:
   ```
   "How do I securely implement [feature] with Stripe to prevent [security concern]?"
   ```

5. **Integration architecture**:
   ```
   "What's the recommended architecture for integrating Stripe [feature] with [tech stack]?"
   ```

## Conclusion

The AI Debugging Assistant provides a powerful way to get technical support for Stripe integration and other programming challenges. By maintaining conversation context and providing code highlighting, it offers a superior experience to standard chat interfaces.

For any script-specific issues, users can refer to the built-in help:

```bash
show_help
```

---

*This guide is intended for AI assistants to help users effectively utilize the AI Debugging Assistant script for technical support, particularly for Stripe integration questions.*
