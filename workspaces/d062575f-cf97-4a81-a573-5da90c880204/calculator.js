// calculator.js

// Function to add two numbers
function add(a, b) {
    return a + b;
}

// Function to subtract two numbers
function subtract(a, b) {
    return a - b;
}

// Function to multiply two numbers
function multiply(a, b) {
    return a * b;
}

// Function to divide two numbers
function divide(a, b) {
    if (b === 0) {
        return "Error: Division by zero";
    }
    return a / b;
}

// Get references to the input fields and buttons
const number1Input = document.getElementById("number1");
const number2Input = document.getElementById("number2");
const addButton = document.getElementById("add");
const subtractButton = document.getElementById("subtract");
const multiplyButton = document.getElementById("multiply");
const divideButton = document.getElementById("divide");
const resultDiv = document.getElementById("result");

// Add event listeners to the buttons
addButton.addEventListener("click", () => {
    calculate(add);
});

subtractButton.addEventListener("click", () => {
    calculate(subtract);
});

multiplyButton.addEventListener("click", () => {
    calculate(multiply);
});

divideButton.addEventListener("click", () => {
    calculate(divide);
});

// Function to perform the calculation and display the result
function calculate(operation) {
    const number1 = parseFloat(number1Input.value);
    const number2 = parseFloat(number2Input.value);

    if (isNaN(number1) || isNaN(number2)) {
        resultDiv.textContent = "Result: Error: Invalid input";
        return;
    }

    const result = operation(number1, number2);
    resultDiv.textContent = `Result: ${result}`;
}

// Make functions available globally for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        add: add,
        subtract: subtract,
        multiply: multiply,
        divide: divide
    };
}