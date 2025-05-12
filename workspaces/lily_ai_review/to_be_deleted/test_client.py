#!/usr/bin/env python3
from llm_client import AIDebugClient

def main():
    # Initialize the client
    client = AIDebugClient(base_url="http://127.0.0.1:9000")
    
    # Ask a question about Stripe
    print("Asking initial question about Stripe webhooks...")
    system_message = "You are a Stripe API expert. Provide detailed, technical answers about Stripe API integration, webhooks, payment processing, subscriptions, and error handling. Include code examples in relevant programming languages when appropriate."
    
    answer, conversation_id = client.ask(
        question="How do I implement idempotency in Stripe webhooks?",
        system_message=system_message,
        model="google/gemini-2.5-flash-preview"
    )
    
    print(f"\nAnswer: {answer[:200]}...\n")
    print(f"Conversation ID: {conversation_id}\n")
    
    # Ask a follow-up question
    print("Asking follow-up question...")
    follow_up_answer, _ = client.ask(
        question="Can you provide a complete code example with idempotency keys?",
        conversation_id=conversation_id
    )
    
    print(f"\nFollow-up answer: {follow_up_answer[:200]}...\n")
    
    # Export the conversation
    print("Exporting conversation to Markdown...")
    content, filename = client.export_conversation(conversation_id, format="markdown")
    
    print(f"Exported to {filename}")
    print(f"Content preview: {content[:200]}...\n")
    
    # Get token usage
    print("Getting token usage statistics...")
    usage = client.get_token_usage()
    
    print(f"Total tokens used: {usage['totals']['total_tokens']}")
    print(f"By model: {usage['by_model']}")
    
if __name__ == "__main__":
    main()
