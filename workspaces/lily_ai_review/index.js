#!/usr/bin/env node

const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const { v4: uuidv4 } = require('uuid');
const { SessionManager } = require('./src/session_manager');

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('openrouter-api-key', {
    alias: 'k',
    type: 'string',
    description: 'OpenRouter API key',
    demandOption: true
  })
  .option('port', {
    alias: 'p',
    type: 'number',
    description: 'Port to run the server on',
    default: 8000
  })
  .option('smaller-model', {
    type: 'string',
    description: 'Model ID for the smaller model',
    default: 'google/gemini-1.5-flash-latest'
  })
  .option('larger-model', {
    type: 'string',
    description: 'Model ID for the larger model',
    default: 'anthropic/claude-3-opus-20240229'
  })
  .option('enable-sessions', {
    type: 'boolean',
    description: 'Enable session-based tools',
    default: false
  })
  .option('session-expiry-minutes', {
    type: 'number',
    description: 'Number of minutes after which a session expires',
    default: 30
  })
  .option('cleanup-interval-minutes', {
    type: 'number',
    description: 'Interval in minutes at which to clean up expired sessions',
    default: 5
  })
  .help()
  .argv;

// Parse enable-sessions flag manually
const enableSessions = process.argv.includes('--enable-sessions=true') || process.argv.includes('--enable-sessions');
console.log('Command line arguments:', process.argv);
console.log('Enable sessions flag:', enableSessions);

// Initialize Express app
const app = express();
app.use(bodyParser.json());

// Initialize session manager if sessions are enabled
const sessionManager = enableSessions
  ? new SessionManager({
      expiryMinutes: argv['session-expiry-minutes'],
      cleanupIntervalMinutes: argv['cleanup-interval-minutes']
    })
  : null;

// Store sessions for the process tool (legacy)
const sessions = new Map();

// OpenRouter API client
const openRouter = axios.create({
  baseURL: 'https://openrouter.ai/api/v1',
  headers: {
    'Authorization': `Bearer ${argv['openrouter-api-key']}`,
    'HTTP-Referer': 'https://github.com/tech-and-ai/ai2ai-mcp',
    'X-Title': 'AI2AI MCP'
  },
  timeout: 60000 // 60 seconds
});

// MCP manifest endpoint
app.get('/mcp/manifest', (req, res) => {
  const tools = [
    {
      name: "feedback",
      description: "Request feedback from a larger model on specific reasoning",
      inputSchema: {
        type: "object",
        properties: {
          context: {
            type: "string",
            description: "Current context or reasoning"
          },
          question: {
            type: "string",
            description: "Specific question or area of uncertainty"
          }
        },
        required: ["context", "question"]
      }
    },
    {
      name: "process",
      description: "Process text through a smaller model with feedback from a larger model when needed",
      inputSchema: {
        type: "object",
        properties: {
          text: {
            type: "string",
            description: "Text to process"
          }
        },
        required: ["text"]
      }
    }
  ];

  // Add session-based tools
  tools.push(
      {
        name: "session.create",
        description: "Create a new session for maintaining context across interactions",
        inputSchema: {
          type: "object",
          properties: {},
          required: []
        }
      },
      {
        name: "session.feedback",
        description: "Request feedback from a larger model with context from previous interactions",
        inputSchema: {
          type: "object",
          properties: {
            sessionId: {
              type: "string",
              description: "ID of the session to use"
            },
            context: {
              type: "string",
              description: "Current context or reasoning"
            },
            question: {
              type: "string",
              description: "Specific question or area of uncertainty"
            }
          },
          required: ["sessionId", "context", "question"]
        }
      },
      {
        name: "session.process",
        description: "Process text through a smaller model with feedback from a larger model when needed, maintaining context from previous interactions",
        inputSchema: {
          type: "object",
          properties: {
            sessionId: {
              type: "string",
              description: "ID of the session to use"
            },
            text: {
              type: "string",
              description: "Text to process"
            }
          },
          required: ["sessionId", "text"]
        }
      },
      {
        name: "session.end",
        description: "End a session and release its resources",
        inputSchema: {
          type: "object",
          properties: {
            sessionId: {
              type: "string",
              description: "ID of the session to end"
            }
          },
          required: ["sessionId"]
        }
      }
    );
  }

  res.json({
    name: "AI2AI Feedback",
    version: "0.1.0",
    description: "AI-to-AI Feedback Protocol for intelligence amplification",
    tools
  });
});

// MCP tools/list endpoint
app.post('/mcp/tools/list', (req, res) => {
  const tools = [
    {
      name: "feedback",
      description: "Request feedback from a larger model on specific reasoning",
      inputSchema: {
        type: "object",
        properties: {
          context: {
            type: "string",
            description: "Current context or reasoning"
          },
          question: {
            type: "string",
            description: "Specific question or area of uncertainty"
          }
        },
        required: ["context", "question"]
      }
    },
    {
      name: "process",
      description: "Process text through a smaller model with feedback from a larger model when needed",
      inputSchema: {
        type: "object",
        properties: {
          text: {
            type: "string",
            description: "Text to process"
          }
        },
        required: ["text"]
      }
    }
  ];

  // Add session-based tools
  tools.push(
      {
        name: "session.create",
        description: "Create a new session for maintaining context across interactions",
        inputSchema: {
          type: "object",
          properties: {},
          required: []
        }
      },
      {
        name: "session.feedback",
        description: "Request feedback from a larger model with context from previous interactions",
        inputSchema: {
          type: "object",
          properties: {
            sessionId: {
              type: "string",
              description: "ID of the session to use"
            },
            context: {
              type: "string",
              description: "Current context or reasoning"
            },
            question: {
              type: "string",
              description: "Specific question or area of uncertainty"
            }
          },
          required: ["sessionId", "context", "question"]
        }
      },
      {
        name: "session.process",
        description: "Process text through a smaller model with feedback from a larger model when needed, maintaining context from previous interactions",
        inputSchema: {
          type: "object",
          properties: {
            sessionId: {
              type: "string",
              description: "ID of the session to use"
            },
            text: {
              type: "string",
              description: "Text to process"
            }
          },
          required: ["sessionId", "text"]
        }
      },
      {
        name: "session.end",
        description: "End a session and release its resources",
        inputSchema: {
          type: "object",
          properties: {
            sessionId: {
              type: "string",
              description: "ID of the session to end"
            }
          },
          required: ["sessionId"]
        }
      }
    );
  }

  res.json({ tools });
});

// MCP tools/call endpoint
app.post('/mcp/tools/call', async (req, res) => {
  const { id, method, params } = req.body;

  if (method !== 'tools/call') {
    return res.status(400).json({
      jsonrpc: "2.0",
      id,
      error: {
        code: -32601,
        message: "Method not found"
      }
    });
  }

  const { name, arguments: args } = params;

  try {
    let result;

    // Handle standard tools
    if (name === 'feedback') {
      result = await handleFeedback(args);
    } else if (name === 'process') {
      result = await handleProcess(args);
    }
    // Handle session-based tools if enabled
    else if (enableSessions) {
      if (name === 'session.create') {
        result = await handleSessionCreate();
      } else if (name === 'session.feedback') {
        result = await handleSessionFeedback(args);
      } else if (name === 'session.process') {
        result = await handleSessionProcess(args);
      } else if (name === 'session.end') {
        result = await handleSessionEnd(args);
      } else {
        return res.status(400).json({
          jsonrpc: "2.0",
          id,
          error: {
            code: -32601,
            message: "Tool not found"
          }
        });
      }
    } else {
      return res.status(400).json({
        jsonrpc: "2.0",
        id,
        error: {
          code: -32601,
          message: "Tool not found"
        }
      });
    }

    res.json({
      jsonrpc: "2.0",
      id,
      result
    });
  } catch (error) {
    console.error('Error handling tool call:', error);
    res.status(500).json({
      jsonrpc: "2.0",
      id,
      error: {
        code: -32000,
        message: error.message || "Internal server error"
      }
    });
  }
});

// Handle feedback tool
async function handleFeedback({ context, question }) {
  console.log(`Requesting feedback for: ${question}`);

  try {
    // Create system prompt for the larger model
    const systemPrompt = `
You are an expert advisor providing feedback to another AI.
Your goal is to help the other AI improve its reasoning and problem-solving.
Provide clear, specific feedback that addresses the question or challenge presented.
Structure your response as follows:

FEEDBACK_SUMMARY: Brief summary of the key issue or insight

REASONING_ASSESSMENT: Evaluate the reasoning approach, identifying strengths and weaknesses

KNOWLEDGE_GAPS: Identify any missing information or knowledge that would help

SUGGESTED_APPROACH: Provide a clear suggestion for how to proceed

ADDITIONAL_CONSIDERATIONS: Mention any other factors that should be considered
`;

    // Create user prompt
    const userPrompt = `
The assistant is working on a problem and has requested feedback. Here is their current reasoning:

${context}

Specific feedback request: ${question}
`;

    // Get feedback from the larger model
    const response = await openRouter.post('/chat/completions', {
      model: argv['larger-model'],
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.3 // Lower temperature for more focused feedback
    });

    const feedback = response.data.choices[0].message.content;

    // Extract structured feedback
    const structured = extractStructuredFeedback(feedback);

    return {
      feedback,
      structured,
      metadata: {
        source_model: argv['larger-model'],
        timestamp: Date.now()
      }
    };
  } catch (error) {
    console.error('Error getting feedback:', error);
    throw new Error(`Failed to get feedback: ${error.message}`);
  }
}

// Handle process tool
async function handleProcess({ text }) {
  console.log(`Processing text: ${text.substring(0, 50)}...`);

  // Generate a session ID if not provided
  const sessionId = uuidv4();

  // Get or create session
  if (!sessions.has(sessionId)) {
    sessions.set(sessionId, {
      id: sessionId,
      history: [],
      createdAt: new Date()
    });
  }

  const session = sessions.get(sessionId);

  try {
    // Add system message if this is a new session
    if (session.history.length === 0) {
      session.history.push({
        role: 'system',
        content: `You are a helpful assistant trying to solve a problem. If you encounter a challenge or are uncertain about your approach, you can ask for feedback by stating 'REQUESTING_FEEDBACK' followed by your specific question or area of uncertainty.`
      });
    }

    // Add user input to conversation
    session.history.push({ role: 'user', content: text });

    // Get response from primary model
    const response = await openRouter.post('/chat/completions', {
      model: argv['smaller-model'],
      messages: session.history,
      temperature: 0.7
    });

    // Extract assistant response
    const assistantResponse = response.data.choices[0].message.content;
    session.history.push({ role: 'assistant', content: assistantResponse });

    // Check if feedback is requested
    if (assistantResponse.includes('REQUESTING_FEEDBACK')) {
      // Extract the feedback request
      const parts = assistantResponse.split('REQUESTING_FEEDBACK');
      if (parts.length < 2) {
        return { response: assistantResponse };
      }

      const feedbackRequest = parts[1].trim();

      // Get feedback from the larger model
      const feedback = await handleFeedback({
        context: assistantResponse,
        question: feedbackRequest
      });

      // Add feedback to conversation
      session.history.push({
        role: 'user',
        content: `Here is feedback on your approach: ${feedback.feedback}`
      });

      // Get updated response from primary model
      const updatedResponse = await openRouter.post('/chat/completions', {
        model: argv['smaller-model'],
        messages: session.history,
        temperature: 0.7
      });

      // Extract updated assistant response
      const finalResponse = updatedResponse.data.choices[0].message.content;
      session.history.push({ role: 'assistant', content: finalResponse });

      return {
        response: finalResponse,
        feedback: feedback.feedback,
        metadata: {
          primary_model: argv['smaller-model'],
          feedback_model: argv['larger-model'],
          timestamp: Date.now()
        }
      };
    }

    // Return the original response if no feedback was requested
    return {
      response: assistantResponse,
      metadata: {
        primary_model: argv['smaller-model'],
        timestamp: Date.now()
      }
    };
  } catch (error) {
    console.error('Error processing text:', error);
    throw new Error(`Failed to process text: ${error.message}`);
  }
}

// Handle session.create tool
async function handleSessionCreate() {
  if (!enableSessions) {
    throw new Error('Session-based tools are not enabled');
  }

  const sessionId = sessionManager.createSession();
  console.log(`Created new session: ${sessionId}`);

  return { sessionId };
}

// Handle session.feedback tool
async function handleSessionFeedback({ sessionId, context, question }) {
  if (!enableSessions) {
    throw new Error('Session-based tools are not enabled');
  }

  // Get the session
  const session = sessionManager.getSession(sessionId);
  if (!session) {
    throw new Error('Session not found or expired');
  }

  console.log(`Requesting feedback for session ${sessionId}: ${question}`);

  try {
    // Add the current interaction to the session history
    session.addInteraction('user', `Context: ${context}\nQuestion: ${question}`);

    // Create system prompt for the larger model
    const systemPrompt = `
You are an expert advisor providing feedback to another AI.
Your goal is to help the other AI improve its reasoning and problem-solving.
Provide clear, specific feedback that addresses the question or challenge presented.
Structure your response as follows:

FEEDBACK_SUMMARY: Brief summary of the key issue or insight

REASONING_ASSESSMENT: Evaluate the reasoning approach, identifying strengths and weaknesses

KNOWLEDGE_GAPS: Identify any missing information or knowledge that would help

SUGGESTED_APPROACH: Provide a clear suggestion for how to proceed

ADDITIONAL_CONSIDERATIONS: Mention any other factors that should be considered

The conversation history is provided for context. Focus on the most recent question.
`;

    // Format the history as a conversation
    const formattedHistory = session.getHistory()
      .filter(entry => entry.role !== 'system')
      .map(entry => {
        const role = entry.role === 'user' ? 'User' : 'Assistant';
        return `${role}: ${entry.content}`;
      }).join('\n\n');

    // Create user prompt with history
    const userPrompt = `
Conversation history:
${formattedHistory}

The assistant is working on a problem and has requested feedback. Here is their current reasoning:

${context}

Specific feedback request: ${question}
`;

    // Get feedback from the larger model
    const response = await openRouter.post('/chat/completions', {
      model: argv['larger-model'],
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.3 // Lower temperature for more focused feedback
    });

    const feedback = response.data.choices[0].message.content;

    // Extract structured feedback
    const structured = extractStructuredFeedback(feedback);

    // Add the response to the session history
    session.addInteraction('assistant', feedback);

    return {
      feedback,
      structured,
      metadata: {
        source_model: argv['larger-model'],
        timestamp: Date.now()
      }
    };
  } catch (error) {
    console.error('Error getting feedback:', error);
    throw new Error(`Failed to get feedback: ${error.message}`);
  }
}

// Handle session.process tool
async function handleSessionProcess({ sessionId, text }) {
  if (!enableSessions) {
    throw new Error('Session-based tools are not enabled');
  }

  // Get the session
  const session = sessionManager.getSession(sessionId);
  if (!session) {
    throw new Error('Session not found or expired');
  }

  console.log(`Processing text for session ${sessionId}: ${text.substring(0, 50)}...`);

  try {
    // Add system message if this is a new session with no history
    if (session.getHistory().length === 0) {
      session.addInteraction('system', `You are a helpful assistant trying to solve a problem. If you encounter a challenge or are uncertain about your approach, you can ask for feedback by stating 'REQUESTING_FEEDBACK' followed by your specific question or area of uncertainty.`);
    }

    // Add user input to conversation
    session.addInteraction('user', text);

    // Get response from primary model
    const response = await openRouter.post('/chat/completions', {
      model: argv['smaller-model'],
      messages: session.getFormattedHistory(),
      temperature: 0.7
    });

    // Extract assistant response
    const assistantResponse = response.data.choices[0].message.content;
    session.addInteraction('assistant', assistantResponse);

    // Check if feedback is requested
    if (assistantResponse.includes('REQUESTING_FEEDBACK')) {
      // Extract the feedback request
      const parts = assistantResponse.split('REQUESTING_FEEDBACK');
      if (parts.length < 2) {
        return { response: assistantResponse };
      }

      const feedbackRequest = parts[1].trim();

      // Get feedback from the larger model
      const feedback = await handleFeedback({
        context: assistantResponse,
        question: feedbackRequest
      });

      // Add feedback to conversation
      session.addInteraction('user', `Here is feedback on your approach: ${feedback.feedback}`);

      // Get updated response from primary model
      const updatedResponse = await openRouter.post('/chat/completions', {
        model: argv['smaller-model'],
        messages: session.getFormattedHistory(),
        temperature: 0.7
      });

      // Extract updated assistant response
      const finalResponse = updatedResponse.data.choices[0].message.content;
      session.addInteraction('assistant', finalResponse);

      return {
        response: finalResponse,
        feedback: feedback.feedback,
        metadata: {
          primary_model: argv['smaller-model'],
          feedback_model: argv['larger-model'],
          timestamp: Date.now()
        }
      };
    }

    // Return the original response if no feedback was requested
    return {
      response: assistantResponse,
      metadata: {
        primary_model: argv['smaller-model'],
        timestamp: Date.now()
      }
    };
  } catch (error) {
    console.error('Error processing text:', error);
    throw new Error(`Failed to process text: ${error.message}`);
  }
}

// Handle session.end tool
async function handleSessionEnd({ sessionId }) {
  if (!enableSessions) {
    throw new Error('Session-based tools are not enabled');
  }

  const success = sessionManager.endSession(sessionId);
  console.log(`Ended session ${sessionId}: ${success}`);

  return { success };
}

// Extract structured feedback from the larger model's response
function extractStructuredFeedback(feedback) {
  const sections = {
    'FEEDBACK_SUMMARY': '',
    'REASONING_ASSESSMENT': '',
    'KNOWLEDGE_GAPS': '',
    'SUGGESTED_APPROACH': '',
    'ADDITIONAL_CONSIDERATIONS': ''
  };

  let currentSection = null;
  const lines = feedback.split('\n');

  for (const line of lines) {
    // Check if this line starts a new section
    for (const section of Object.keys(sections)) {
      if (line.includes(section)) {
        currentSection = section;
        break;
      }
    }

    // Add content to current section if we're in one
    if (currentSection && line && !line.includes(currentSection)) {
      sections[currentSection] += line + '\n';
    }
  }

  // Clean up each section (remove extra whitespace)
  for (const section in sections) {
    sections[section] = sections[section].trim();
  }

  return sections;
}

// Start the server
console.log('Enable sessions value:', enableSessions);
console.log('Enable sessions type:', typeof enableSessions);
const server = app.listen(argv.port, () => {
  console.log(`AI2AI MCP Server running on port ${argv.port}`);
  if (enableSessions) {
    console.log(`Session-based tools enabled (expiry: ${argv['session-expiry-minutes']} minutes, cleanup interval: ${argv['cleanup-interval-minutes']} minutes)`);
  }
});

// Handle termination signals
process.on('SIGINT', () => {
  console.log('Received SIGINT. Shutting down...');
  if (enableSessions && sessionManager) {
    sessionManager.stopCleanupInterval();
  }
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('Received SIGTERM. Shutting down...');
  if (enableSessions && sessionManager) {
    sessionManager.stopCleanupInterval();
  }
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});
