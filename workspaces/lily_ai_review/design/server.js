/**
 * Session-Based AI2AI Feedback MCP Server
 * 
 * This module initializes the Session-Based AI2AI Feedback MCP Server.
 */

const { createServer } = require('http');
const { Server } = require('mcp'); // Assuming this is the MCP server package
const { getConfig } = require('./config');
const { initializeSessionTools } = require('./session_tools');
const { initializeAI2AI } = require('../src/ai2ai'); // Assuming this is the existing AI2AI module

/**
 * Initialize the MCP server
 * @returns {Object} The MCP server instance
 */
function initializeServer() {
  // Get configuration options
  const config = getConfig();

  // Create an HTTP server
  const httpServer = createServer();

  // Create an MCP server
  const server = new Server({
    name: 'AI2AI Feedback',
    version: '0.1.0',
    description: 'AI-to-AI Feedback Protocol for intelligence amplification',
    httpServer
  });

  // Initialize the AI2AI module
  initializeAI2AI({
    openrouterApiKey: config.openrouterApiKey,
    smallerModel: config.smallerModel,
    largerModel: config.largerModel
  });

  // Register the standard AI2AI tools
  registerStandardTools(server);

  // Initialize session-based tools if enabled
  if (config.enableSessions) {
    initializeSessionTools(server, {
      expiryMinutes: config.sessionExpiryMinutes,
      cleanupIntervalMinutes: config.cleanupIntervalMinutes
    });
  }

  return { server, httpServer, config };
}

/**
 * Register the standard AI2AI tools with the MCP server
 * @param {Object} server - The MCP server instance
 */
function registerStandardTools(server) {
  // Register the feedback tool
  server.addTool({
    name: 'feedback',
    description: 'Request feedback from a larger model on specific reasoning',
    inputSchema: {
      type: 'object',
      properties: {
        context: {
          type: 'string',
          description: 'Current context or reasoning'
        },
        question: {
          type: 'string',
          description: 'Specific question or area of uncertainty'
        }
      },
      required: ['context', 'question']
    },
    handler: async ({ context, question }) => {
      const feedback = await getFeedback(context, question);
      return { feedback };
    }
  });

  // Register the process tool
  server.addTool({
    name: 'process',
    description: 'Process text through a smaller model with feedback from a larger model when needed',
    inputSchema: {
      type: 'object',
      properties: {
        text: {
          type: 'string',
          description: 'Text to process'
        }
      },
      required: ['text']
    },
    handler: async ({ text }) => {
      const response = await processText(text);
      return { response };
    }
  });
}

/**
 * Start the server
 */
function startServer() {
  const { server, httpServer, config } = initializeServer();

  // Start the server
  httpServer.listen(config.port, () => {
    console.log(`AI2AI MCP Server running on port ${config.port}`);
  });

  // Handle errors
  httpServer.on('error', (error) => {
    console.error('Server error:', error);
  });

  // Handle shutdown
  process.on('SIGINT', () => {
    console.log('Shutting down server...');
    httpServer.close(() => {
      console.log('Server shut down');
      process.exit(0);
    });
  });

  return { server, httpServer };
}

// Start the server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = {
  initializeServer,
  startServer
};
