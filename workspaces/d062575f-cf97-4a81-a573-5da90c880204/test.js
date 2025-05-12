// test.js
const { add, subtract, multiply, divide, calculate } = require('./script');

// Mock the document object for testing in a Node.js environment
global.document = {
    getElementById: (id) => {
        return {
            value: '',
            textContent: ''
        };
    }
};


describe('Calculator Functions', () => {
    beforeEach(() => {
        // Reset the mock implementation before each test
        document.getElementById = jest.fn((id) => {
            return {
                value: '',
                textContent: ''
            };
        });
    });

    test('add should add two numbers', () => {
        document.getElementById = jest.fn((id) => {
            if (id === 'num1') return { value: '5' };
            if (id === 'num2') return { value: '3' };
            return { value: '', textContent: '' };
        });
        const resultElement = { textContent: '' };
        document.getElementById = jest.fn().mockReturnValueOnce({ value: '5' }).mockReturnValueOnce({ value: '3' }).mockReturnValue(resultElement);
        calculate('+');
        expect(resultElement.textContent).toBe('Result: 8.00');
    });

    test('subtract should subtract two numbers', () => {
        document.getElementById = jest.fn((id) => {
            if (id === 'num1') return { value: '5' };
            if (id === 'num2') return { value: '3' };
            return { value: '', textContent: '' };
        });
        const resultElement = { textContent: '' };
        document.getElementById = jest.fn().mockReturnValueOnce({ value: '5' }).mockReturnValueOnce({ value: '3' }).mockReturnValue(resultElement);
        calculate('-');
        expect(resultElement.textContent).toBe('Result: 2.00');
    });

    test('multiply should multiply two numbers', () => {
        document.getElementById = jest.fn((id) => {
            if (id === 'num1') return { value: '5' };
            if (id === 'num2') return { value: '3' };
            return { value: '', textContent: '' };
        });
        const resultElement = { textContent: '' };
        document.getElementById = jest.fn().mockReturnValueOnce({ value: '5' }).mockReturnValueOnce({ value: '3' }).mockReturnValue(resultElement);
        calculate('*');
        expect(resultElement.textContent).toBe('Result: 15.00');
    });

    test('divide should divide two numbers', () => {
        document.getElementById = jest.fn((id) => {
            if (id === 'num1') return { value: '6' };
            if (id === 'num2') return { value: '3' };
            return { value: '', textContent: '' };
        });
        const resultElement = { textContent: '' };
        document.getElementById = jest.fn().mockReturnValueOnce({ value: '6' }).mockReturnValueOnce({ value: '3' }).mockReturnValue(resultElement);
        calculate('/');
        expect(resultElement.textContent).toBe('Result: 2.00');
    });

    test('divide should handle division by zero', () => {
        document.getElementById = jest.fn((id) => {
            if (id === 'num1') return { value: '6' };
            if (id === 'num2') return { value: '0' };
            return { value: '', textContent: '' };
        });
        const errorMessageElement = { textContent: '' };
        document.getElementById = jest.fn().mockReturnValueOnce({ value: '6' }).mockReturnValueOnce({ value: '0' }).mockReturnValue(errorMessageElement);
        calculate('/');
        expect(errorMessageElement.textContent).toBe('Division by zero is not allowed.');
    });

    test('calculate should handle invalid input', () => {
        document.getElementById = jest.fn((id) => {
            if (id === 'num1') return { value: 'abc' };
            if (id === 'num2') return { value: '3' };
            return { value: '', textContent: '' };
        });
        const errorMessageElement = { textContent: '' };
        document.getElementById = jest.fn().mockReturnValueOnce({ value: 'abc' }).mockReturnValueOnce({ value: '3' }).mockReturnValue(errorMessageElement);
        calculate('+');
        expect(errorMessageElement.textContent).toBe('Please enter valid numbers.');
    });
});