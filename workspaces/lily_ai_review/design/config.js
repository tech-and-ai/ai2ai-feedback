/**
 * Configuration for Session-Based AI2AI Feedback MCP Server
 * 
 * This module provides configuration options for the Session-Based AI2AI Feedback MCP Server.
 */

/**
 * Parse command line arguments
 * @returns {Object} The parsed command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    openrouterApiKey: null,
    smallerModel: 'google/gemini-2.0-flash-001',
    largerModel: 'google/gemini-2.0-flash-001',
    enableSessions: false,
    sessionExpiryMinutes: 30,
    cleanupIntervalMinutes: 5,
    port: 8000
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg.startsWith('--openrouter-api-key=')) {
      options.openrouterApiKey = arg.split('=')[1];
    } else if (arg.startsWith('--smaller-model=')) {
      options.smallerModel = arg.split('=')[1];
    } else if (arg.startsWith('--larger-model=')) {
      options.largerModel = arg.split('=')[1];
    } else if (arg.startsWith('--enable-sessions=')) {
      options.enableSessions = arg.split('=')[1] === 'true';
    } else if (arg.startsWith('--session-expiry-minutes=')) {
      options.sessionExpiryMinutes = parseInt(arg.split('=')[1], 10);
    } else if (arg.startsWith('--cleanup-interval-minutes=')) {
      options.cleanupIntervalMinutes = parseInt(arg.split('=')[1], 10);
    } else if (arg.startsWith('--port=')) {
      options.port = parseInt(arg.split('=')[1], 10);
    }
  }

  return options;
}

/**
 * Validate configuration options
 * @param {Object} options - The configuration options
 * @throws {Error} If any required options are missing or invalid
 */
function validateConfig(options) {
  if (!options.openrouterApiKey) {
    throw new Error('OpenRouter API key is required');
  }

  if (!options.smallerModel) {
    throw new Error('Smaller model is required');
  }

  if (!options.largerModel) {
    throw new Error('Larger model is required');
  }

  if (options.enableSessions) {
    if (options.sessionExpiryMinutes <= 0) {
      throw new Error('Session expiry minutes must be greater than 0');
    }

    if (options.cleanupIntervalMinutes <= 0) {
      throw new Error('Cleanup interval minutes must be greater than 0');
    }
  }

  if (options.port <= 0 || options.port > 65535) {
    throw new Error('Port must be between 1 and 65535');
  }
}

/**
 * Get configuration options
 * @returns {Object} The configuration options
 */
function getConfig() {
  const options = parseArgs();
  validateConfig(options);
  return options;
}

module.exports = {
  getConfig
};
