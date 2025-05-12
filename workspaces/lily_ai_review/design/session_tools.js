/**
 * Session-Based Tools for AI2AI Feedback MCP Server
 * 
 * This module provides session-based tools for the AI2AI Feedback MCP Server.
 * These tools allow for maintaining context across multiple interactions.
 */

const { SessionManager } = require('./session_manager');
const { getFeedback, processText } = require('../src/ai2ai'); // Assuming this is the existing AI2AI module

/**
 * Initialize session-based tools
 * @param {Object} server - The MCP server instance
 * @param {Object} options - Configuration options
 * @param {number} options.expiryMinutes - The number of minutes after which a session expires
 * @param {number} options.cleanupIntervalMinutes - The interval in minutes at which to clean up expired sessions
 * @returns {Object} The session manager instance
 */
function initializeSessionTools(server, options = {}) {
  // Create a session manager
  const sessionManager = new SessionManager(options);

  // Register session-based tools
  registerSessionTools(server, sessionManager);

  return sessionManager;
}

/**
 * Register session-based tools with the MCP server
 * @param {Object} server - The MCP server instance
 * @param {SessionManager} sessionManager - The session manager instance
 */
function registerSessionTools(server, sessionManager) {
  // Register session.create tool
  server.addTool({
    name: 'session.create',
    description: 'Create a new session for maintaining context across interactions',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    },
    handler: async () => {
      const sessionId = sessionManager.createSession();
      return { sessionId };
    }
  });

  // Register session.feedback tool
  server.addTool({
    name: 'session.feedback',
    description: 'Request feedback from a larger model with context from previous interactions',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: {
          type: 'string',
          description: 'ID of the session to use'
        },
        context: {
          type: 'string',
          description: 'Current context or reasoning'
        },
        question: {
          type: 'string',
          description: 'Specific question or area of uncertainty'
        }
      },
      required: ['sessionId', 'context', 'question']
    },
    handler: async ({ sessionId, context, question }) => {
      // Get the session
      const session = sessionManager.getSession(sessionId);
      if (!session) {
        throw new Error('Session not found or expired');
      }

      // Add the current interaction to the session history
      session.addInteraction('user', `Context: ${context}\nQuestion: ${question}`);

      // Get the conversation history
      const history = session.getHistory();

      // Use the history to provide context to the model
      const feedback = await getFeedbackWithHistory(history, context, question);

      // Add the response to the session history
      session.addInteraction('assistant', JSON.stringify(feedback));

      return { feedback };
    }
  });

  // Register session.process tool
  server.addTool({
    name: 'session.process',
    description: 'Process text through a smaller model with feedback from a larger model when needed, maintaining context from previous interactions',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: {
          type: 'string',
          description: 'ID of the session to use'
        },
        text: {
          type: 'string',
          description: 'Text to process'
        }
      },
      required: ['sessionId', 'text']
    },
    handler: async ({ sessionId, text }) => {
      // Get the session
      const session = sessionManager.getSession(sessionId);
      if (!session) {
        throw new Error('Session not found or expired');
      }

      // Add the current interaction to the session history
      session.addInteraction('user', text);

      // Get the conversation history
      const history = session.getHistory();

      // Use the history to provide context to the model
      const response = await processTextWithHistory(history, text);

      // Add the response to the session history
      session.addInteraction('assistant', response);

      return { response };
    }
  });

  // Register session.end tool
  server.addTool({
    name: 'session.end',
    description: 'End a session and release its resources',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: {
          type: 'string',
          description: 'ID of the session to end'
        }
      },
      required: ['sessionId']
    },
    handler: async ({ sessionId }) => {
      const success = sessionManager.endSession(sessionId);
      return { success };
    }
  });
}

/**
 * Get feedback with conversation history
 * @param {Array} history - The conversation history
 * @param {string} context - The current context
 * @param {string} question - The current question
 * @returns {Object} The feedback
 */
async function getFeedbackWithHistory(history, context, question) {
  // Format the history as a conversation
  const formattedHistory = formatHistoryForModel(history);

  // Append the current context and question
  const fullContext = `${formattedHistory}\n\nCurrent Context: ${context}\nQuestion: ${question}`;

  // Get feedback using the existing getFeedback function
  return await getFeedback(fullContext, question);
}

/**
 * Process text with conversation history
 * @param {Array} history - The conversation history
 * @param {string} text - The text to process
 * @returns {string} The processed text
 */
async function processTextWithHistory(history, text) {
  // Format the history as a conversation
  const formattedHistory = formatHistoryForModel(history);

  // Append the current text
  const fullText = `${formattedHistory}\n\nCurrent Text: ${text}`;

  // Process the text using the existing processText function
  return await processText(fullText);
}

/**
 * Format conversation history for the model
 * @param {Array} history - The conversation history
 * @returns {string} The formatted history
 */
function formatHistoryForModel(history) {
  return history.map(entry => {
    const role = entry.role === 'user' ? 'User' : 'Assistant';
    return `${role}: ${entry.content}`;
  }).join('\n\n');
}

module.exports = {
  initializeSessionTools
};
