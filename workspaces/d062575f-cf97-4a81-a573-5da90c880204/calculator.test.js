// calculator.test.js
const { add, subtract, multiply, divide } = require('./script');

// Test addition
test('adds 1 + 2 to equal 3', () => {
  expect(add(1, 2)).toBe(3);
});

// Test subtraction
test('subtracts 2 - 1 to equal 1', () => {
  expect(subtract(2, 1)).toBe(1);
});

// Test multiplication
test('multiplies 1 * 2 to equal 2', () => {
  expect(multiply(1, 2)).toBe(2);
});

// Test division
test('divides 4 / 2 to equal 2', () => {
  expect(divide(4, 2)).toBe(2);
});

// Test division by zero
test('divides by zero', () => {
  expect(divide(5, 0)).toBe('Cannot divide by zero');
});