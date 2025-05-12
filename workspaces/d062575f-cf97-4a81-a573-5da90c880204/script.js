// script.js

function add() {
    calculate('+');
}

function subtract() {
    calculate('-');n}

function multiply() {
    calculate('*');
}

function divide() {
    calculate('/');
}

function calculate(operation) {
    const num1 = parseFloat(document.getElementById('num1').value);
    const num2 = parseFloat(document.getElementById('num2').value);
    const errorMessageDiv = document.getElementById('error-message');
    errorMessageDiv.textContent = ''; // Clear previous error messages

    if (isNaN(num1) || isNaN(num2)) {
        errorMessageDiv.textContent = 'Please enter valid numbers.';
        document.getElementById('result').textContent = 'Result:';
        return;
    }

    let result;
    try {
        switch (operation) {
            case '+':
                result = num1 + num2;
                break;
            case '-':
                result = num1 - num2;
                break;
            case '*':
                result = num1 * num2;
                break;
            case '/':
                if (num2 === 0) {
                    throw new Error('Division by zero is not allowed.');
                }
                result = num1 / num2;
                break;
            default:
                throw new Error('Invalid operation.');
        }

        document.getElementById('result').textContent = 'Result: ' + result.toFixed(2);
    } catch (error) {
        errorMessageDiv.textContent = error.message;
        document.getElementById('result').textContent = 'Result:';
    }
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        add: add,
        subtract: subtract,
        multiply: multiply,
        divide: divide,
        calculate: calculate
    };
}