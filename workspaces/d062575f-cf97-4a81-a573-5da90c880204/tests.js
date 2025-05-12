// Test functions
function testAddition() {
  display.value = '2+2';
  calculate();
  console.assert(display.value === '4', 'Addition test failed');
}

function testSubtraction() {
  display.value = '5-3';
  calculate();
  console.assert(display.value === '2', 'Subtraction test failed');
}

function testMultiplication() {
  display.value = '3*4';
  calculate();
  console.assert(display.value === '12', 'Multiplication test failed');
}

function testDivision() {
  display.value = '10/2';
  calculate();
  console.assert(display.value === '5', 'Division test failed');
}

function testDivisionByZero() {
  display.value = '5/0';
  calculate();
  console.assert(display.value === 'Infinity', 'Division by zero test failed');
}

// Run tests
testAddition();
testSubtraction();
testMultiplication();
testDivision();
testDivisionByZero();

console.log('All tests completed.');