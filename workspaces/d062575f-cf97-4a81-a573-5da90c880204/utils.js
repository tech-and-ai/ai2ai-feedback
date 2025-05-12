// Function to perform the calculation
import { add, subtract, multiply, divide } from './utils.js';

function operate(operation) {
    const num1 = parseFloat(document.getElementById('num1').value);
    const num2 = parseFloat(document.getElementById('num2').value);

    // Input validation
    if (isNaN(num1) || isNaN(num2)) {
        displayResult('Please enter valid numbers.');
        return;
    }

    let result;

    switch (operation) {
        case 'add':
            result = add(num1, num2);
            break;
        case 'subtract':
            result = subtract(num1, num2);
            break;
        case 'multiply':
            result = multiply(num1, num2);
            break;
        case 'divide':
            if (num2 === 0) {
                displayResult('Cannot divide by zero.');
                return;
            }
            result = divide(num1, num2);
            break;
        default:
            displayResult('Invalid operation.');
            return;
    }

    displayResult(result);
}

// Function to display the result
function displayResult(result) {
    document.getElementById('result').innerText = result;
}