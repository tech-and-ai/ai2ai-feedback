/**
 * Test script for Session-Based AI2AI Feedback Tool
 * 
 * This script demonstrates how to use the Session-Based AI2AI Feedback Tool.
 */

const axios = require('axios');

// Configuration
const SERVER_URL = 'http://192.168.0.184:8000';

/**
 * Call an MCP tool
 * @param {string} name - The name of the tool to call
 * @param {Object} arguments - The arguments to pass to the tool
 * @returns {Promise<Object>} The tool response
 */
async function callTool(name, arguments = {}) {
  try {
    const response = await axios.post(`${SERVER_URL}/mcp/tools/call`, {
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name,
        arguments
      }
    });

    return response.data.result;
  } catch (error) {
    console.error('Error calling tool:', error.response?.data || error.message);
    throw error;
  }
}

/**
 * Main function
 */
async function main() {
  try {
    console.log('Creating a session...');
    const createResponse = await callTool('session.create');
    const sessionId = createResponse.sessionId;
    console.log(`Session created with ID: ${sessionId}`);

    console.log('\nAsking about Fibonacci optimization...');
    const feedback1 = await callTool('session.feedback', {
      sessionId,
      context: 'I am trying to optimize a recursive Fibonacci algorithm, but it is very slow for large numbers.',
      question: 'How can I improve the performance of this recursive algorithm?'
    });
    console.log('Feedback received:');
    console.log(JSON.stringify(feedback1.feedback, null, 2));

    console.log('\nAsking about memoization time complexity...');
    const feedback2 = await callTool('session.feedback', {
      sessionId,
      context: 'I implemented the memoization approach as you suggested, but I am wondering about the time complexity.',
      question: 'What is the time complexity of the memoized Fibonacci algorithm compared to the original recursive algorithm?'
    });
    console.log('Feedback received:');
    console.log(JSON.stringify(feedback2.feedback, null, 2));

    console.log('\nAsking about iterative approach...');
    const feedback3 = await callTool('session.feedback', {
      sessionId,
      context: 'I understand the time complexity now. I am also considering an iterative approach. Would that be even better?',
      question: 'How does the iterative approach compare to the memoized recursive approach in terms of performance?'
    });
    console.log('Feedback received:');
    console.log(JSON.stringify(feedback3.feedback, null, 2));

    console.log('\nEnding the session...');
    const endResponse = await callTool('session.end', {
      sessionId
    });
    console.log(`Session ended: ${endResponse.success}`);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run the main function
main();
