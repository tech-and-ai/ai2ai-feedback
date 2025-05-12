/**
 * Session Manager for AI2AI Feedback MCP Server
 * 
 * This module provides session management functionality for the AI2AI Feedback MCP Server.
 * It allows for creating, retrieving, updating, and deleting sessions, as well as
 * automatically cleaning up expired sessions.
 */

const { v4: uuidv4 } = require('uuid');

/**
 * Session class representing a conversation session
 */
class Session {
  /**
   * Create a new session
   * @param {string} sessionId - The unique identifier for the session
   */
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.createdAt = new Date();
    this.lastAccessedAt = new Date();
    this.history = [];
  }

  /**
   * Add an interaction to the session history
   * @param {string} role - The role of the participant (user or assistant)
   * @param {string} content - The content of the interaction
   */
  addInteraction(role, content) {
    this.history.push({
      role,
      content,
      timestamp: new Date()
    });
    this.lastAccessedAt = new Date();
  }

  /**
   * Get the session history
   * @returns {Array} The session history
   */
  getHistory() {
    return this.history;
  }

  /**
   * Check if the session has expired
   * @param {number} expiryMinutes - The number of minutes after which a session expires
   * @returns {boolean} True if the session has expired, false otherwise
   */
  isExpired(expiryMinutes) {
    const expiryTime = new Date(this.lastAccessedAt);
    expiryTime.setMinutes(expiryTime.getMinutes() + expiryMinutes);
    return new Date() > expiryTime;
  }
}

/**
 * SessionManager class for managing sessions
 */
class SessionManager {
  /**
   * Create a new SessionManager
   * @param {Object} options - Configuration options
   * @param {number} options.expiryMinutes - The number of minutes after which a session expires
   * @param {number} options.cleanupIntervalMinutes - The interval in minutes at which to clean up expired sessions
   */
  constructor(options = {}) {
    this.sessions = new Map();
    this.expiryMinutes = options.expiryMinutes || 30;
    this.cleanupIntervalMinutes = options.cleanupIntervalMinutes || 5;
    
    // Start the cleanup interval
    this.startCleanupInterval();
  }

  /**
   * Start the cleanup interval
   * @private
   */
  startCleanupInterval() {
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpiredSessions();
    }, this.cleanupIntervalMinutes * 60 * 1000);
  }

  /**
   * Stop the cleanup interval
   */
  stopCleanupInterval() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }

  /**
   * Create a new session
   * @returns {string} The session ID
   */
  createSession() {
    const sessionId = uuidv4();
    const session = new Session(sessionId);
    this.sessions.set(sessionId, session);
    return sessionId;
  }

  /**
   * Get a session by ID
   * @param {string} sessionId - The session ID
   * @returns {Session|null} The session, or null if not found or expired
   */
  getSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return null;
    }
    
    if (session.isExpired(this.expiryMinutes)) {
      this.endSession(sessionId);
      return null;
    }
    
    return session;
  }

  /**
   * End a session
   * @param {string} sessionId - The session ID
   * @returns {boolean} True if the session was ended, false otherwise
   */
  endSession(sessionId) {
    return this.sessions.delete(sessionId);
  }

  /**
   * Clean up expired sessions
   */
  cleanupExpiredSessions() {
    for (const [sessionId, session] of this.sessions.entries()) {
      if (session.isExpired(this.expiryMinutes)) {
        this.sessions.delete(sessionId);
      }
    }
  }

  /**
   * Get the number of active sessions
   * @returns {number} The number of active sessions
   */
  getSessionCount() {
    return this.sessions.size;
  }
}

module.exports = {
  Session,
  SessionManager
};
