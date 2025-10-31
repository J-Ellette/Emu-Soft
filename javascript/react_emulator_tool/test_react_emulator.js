/**
 * Test Suite for React Emulator
 * 
 * This file tests the React emulator implementation to ensure all features
 * work correctly including components, hooks, rendering, and utilities.
 */

const React = require('./react_emulator');

// Helper function to test
function assertEqual(actual, expected, message) {
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
        console.error(`✗ ${message}`);
        console.error(`  Expected: ${JSON.stringify(expected)}`);
        console.error(`  Actual: ${JSON.stringify(actual)}`);
        return false;
    }
    console.log(`✓ ${message}`);
    return true;
}

function assertContains(actual, substring, message) {
    if (!actual.includes(substring)) {
        console.error(`✗ ${message}`);
        console.error(`  Expected to contain: ${substring}`);
        console.error(`  Actual: ${actual}`);
        return false;
    }
    console.log(`✓ ${message}`);
    return true;
}

let passedTests = 0;
let totalTests = 0;

function runTest(testFn, testName) {
    totalTests++;
    try {
        const result = testFn();
        if (result !== false) {
            passedTests++;
        }
    } catch (error) {
        console.error(`✗ ${testName}`);
        console.error(`  Error: ${error.message}`);
    }
}

console.log('Running React Emulator Tests...\n');

// Test 1: createElement
console.log('=== createElement Tests ===');
runTest(() => {
    const element = React.createElement('div', { id: 'test' }, 'Hello');
    return assertEqual(element.type, 'div', 'createElement creates element with correct type') &&
           assertEqual(element.props.id, 'test', 'createElement preserves props') &&
           assertEqual(element.props.children, 'Hello', 'createElement includes children');
}, 'createElement');

runTest(() => {
    const element = React.createElement('div', null, 'Child1', 'Child2');
    return assertEqual(element.props.children.length, 2, 'createElement handles multiple children');
}, 'createElement with multiple children');

// Test 2: Component class
console.log('\n=== Component Class Tests ===');
runTest(() => {
    class TestComponent extends React.Component {
        render() {
            return React.createElement('div', null, 'Test');
        }
    }
    
    const component = new TestComponent({ name: 'test' });
    assertEqual(component.props.name, 'test', 'Component receives props');
    return true;
}, 'Component class props');

runTest(() => {
    class TestComponent extends React.Component {
        constructor(props) {
            super(props);
            this.state = { count: 0 };
        }
        
        render() {
            return React.createElement('div', null, this.state.count);
        }
    }
    
    const component = new TestComponent({});
    component.setState({ count: 5 });
    return assertEqual(component.state.count, 5, 'setState updates state');
}, 'Component setState');

// Test 3: Function components
console.log('\n=== Function Component Tests ===');
runTest(() => {
    function Greeting({ name }) {
        return React.createElement('h1', null, `Hello, ${name}`);
    }
    
    const rendered = React.renderComponent(Greeting, { name: 'World' });
    return assertEqual(rendered.props.children, 'Hello, World', 'Function component renders correctly');
}, 'Function component');

// Test 4: useState hook
console.log('\n=== useState Hook Tests ===');
runTest(() => {
    function Counter() {
        const [count, setCount] = React.useState(0);
        return React.createElement('div', null, count);
    }
    
    const rendered = React.renderComponent(Counter, {});
    return assertEqual(rendered.props.children, 0, 'useState initializes with initial value');
}, 'useState initialization');

runTest(() => {
    function Counter() {
        const [count, setCount] = React.useState(() => 5);
        return React.createElement('div', null, count);
    }
    
    const rendered = React.renderComponent(Counter, {});
    return assertEqual(rendered.props.children, 5, 'useState accepts initializer function');
}, 'useState with initializer function');

// Test 5: useEffect hook
console.log('\n=== useEffect Hook Tests ===');
runTest(() => {
    let effectRan = false;
    
    function Component() {
        React.useEffect(() => {
            effectRan = true;
        }, []);
        return React.createElement('div', null, 'Test');
    }
    
    React.renderComponent(Component, {});
    return assertEqual(effectRan, true, 'useEffect runs effect');
}, 'useEffect execution');

// Test 6: useRef hook
console.log('\n=== useRef Hook Tests ===');
runTest(() => {
    function Component() {
        const ref = React.useRef(10);
        return React.createElement('div', null, ref.current);
    }
    
    const rendered = React.renderComponent(Component, {});
    return assertEqual(rendered.props.children, 10, 'useRef creates ref with initial value');
}, 'useRef initialization');

// Test 7: useMemo hook
console.log('\n=== useMemo Hook Tests ===');
runTest(() => {
    function Component() {
        const expensive = React.useMemo(() => {
            return 2 + 2;
        }, []);
        return React.createElement('div', null, expensive);
    }
    
    const rendered = React.renderComponent(Component, {});
    return assertEqual(rendered.props.children, 4, 'useMemo computes value');
}, 'useMemo computation');

// Test 8: useCallback hook
console.log('\n=== useCallback Hook Tests ===');
runTest(() => {
    function Component() {
        const callback = React.useCallback(() => 'hello', []);
        return React.createElement('div', null, callback());
    }
    
    const rendered = React.renderComponent(Component, {});
    return assertEqual(rendered.props.children, 'hello', 'useCallback memoizes function');
}, 'useCallback memoization');

// Test 9: useReducer hook
console.log('\n=== useReducer Hook Tests ===');
runTest(() => {
    function reducer(state, action) {
        switch (action.type) {
            case 'increment':
                return { count: state.count + 1 };
            case 'decrement':
                return { count: state.count - 1 };
            default:
                return state;
        }
    }
    
    function Component() {
        const [state, dispatch] = React.useReducer(reducer, { count: 0 });
        return React.createElement('div', null, state.count);
    }
    
    const rendered = React.renderComponent(Component, {});
    return assertEqual(rendered.props.children, 0, 'useReducer initializes state');
}, 'useReducer initialization');

// Test 10: createContext
console.log('\n=== Context Tests ===');
runTest(() => {
    const ThemeContext = React.createContext('light');
    assertEqual(ThemeContext._currentValue, 'light', 'createContext sets default value');
    return true;
}, 'createContext');

runTest(() => {
    const ThemeContext = React.createContext('light');
    
    function Consumer() {
        const theme = React.useContext(ThemeContext);
        return React.createElement('div', null, theme);
    }
    
    ThemeContext._currentValue = 'dark';
    const rendered = React.renderComponent(Consumer, {});
    return assertEqual(rendered.props.children, 'dark', 'useContext reads context value');
}, 'useContext');

// Test 11: createRef
console.log('\n=== Ref Tests ===');
runTest(() => {
    const ref = React.createRef();
    assertEqual(ref.current, null, 'createRef creates ref with null');
    ref.current = 'test';
    return assertEqual(ref.current, 'test', 'createRef allows setting current');
}, 'createRef');

// Test 12: Fragment
console.log('\n=== Fragment Tests ===');
runTest(() => {
    const fragment = React.Fragment({ 
        children: [
            React.createElement('div', null, 'Child1'),
            React.createElement('div', null, 'Child2')
        ] 
    });
    return assertEqual(fragment.length, 2, 'Fragment returns children array');
}, 'Fragment');

// Test 13: Children utilities
console.log('\n=== Children Utilities Tests ===');
runTest(() => {
    const children = ['a', 'b', 'c'];
    const mapped = React.Children.map(children, (child, index) => child.toUpperCase());
    return assertEqual(mapped, ['A', 'B', 'C'], 'Children.map transforms children');
}, 'Children.map');

runTest(() => {
    const children = ['a', 'b', 'c'];
    const count = React.Children.count(children);
    return assertEqual(count, 3, 'Children.count returns correct count');
}, 'Children.count');

runTest(() => {
    const child = 'single';
    const only = React.Children.only(child);
    return assertEqual(only, 'single', 'Children.only returns single child');
}, 'Children.only');

// Test 14: cloneElement
console.log('\n=== cloneElement Tests ===');
runTest(() => {
    const original = React.createElement('div', { id: 'test' }, 'Hello');
    const cloned = React.cloneElement(original, { className: 'new' });
    
    return assertEqual(cloned.props.id, 'test', 'cloneElement preserves original props') &&
           assertEqual(cloned.props.className, 'new', 'cloneElement adds new props');
}, 'cloneElement');

// Test 15: isValidElement
console.log('\n=== isValidElement Tests ===');
runTest(() => {
    const element = React.createElement('div', null, 'Test');
    return assertEqual(React.isValidElement(element), true, 'isValidElement returns true for React element');
}, 'isValidElement for React element');

runTest(() => {
    return assertEqual(React.isValidElement({}), false, 'isValidElement returns false for plain object');
}, 'isValidElement for plain object');

// Test 16: renderToString
console.log('\n=== renderToString Tests ===');
runTest(() => {
    const element = React.createElement('div', { id: 'test' }, 'Hello');
    const html = React.renderToString(element);
    return assertContains(html, '<div', 'renderToString generates HTML') &&
           assertContains(html, 'id="test"', 'renderToString includes attributes') &&
           assertContains(html, 'Hello', 'renderToString includes children');
}, 'renderToString');

runTest(() => {
    function Greeting({ name }) {
        return React.createElement('h1', null, `Hello, ${name}`);
    }
    
    const element = React.createElement(Greeting, { name: 'World' });
    const html = React.renderToString(element);
    
    return assertContains(html, '<h1>', 'renderToString renders component') &&
           assertContains(html, 'Hello, World', 'renderToString includes component output');
}, 'renderToString with component');

// Test 17: memo
console.log('\n=== memo Tests ===');
runTest(() => {
    function Component({ value }) {
        return React.createElement('div', null, value);
    }
    
    const MemoizedComponent = React.memo(Component);
    return assertEqual(MemoizedComponent._isMemoized, true, 'memo marks component as memoized');
}, 'memo HOC');

// Test 18: Real-world example - Counter component
console.log('\n=== Real-World Examples ===');
runTest(() => {
    function Counter() {
        const [count, setCount] = React.useState(0);
        
        return React.createElement('div', null,
            React.createElement('p', null, `Count: ${count}`),
            React.createElement('button', { onClick: () => setCount(count + 1) }, 'Increment')
        );
    }
    
    const rendered = React.renderComponent(Counter, {});
    const html = React.renderToString(rendered);
    
    return assertContains(html, 'Count: 0', 'Counter component renders initial count');
}, 'Counter component');

// Test 19: Real-world example - Todo list
runTest(() => {
    function TodoList() {
        const [todos] = React.useState([
            { id: 1, text: 'Learn React' },
            { id: 2, text: 'Build app' }
        ]);
        
        return React.createElement('ul', null,
            todos.map(todo => 
                React.createElement('li', { key: todo.id }, todo.text)
            )
        );
    }
    
    const rendered = React.renderComponent(TodoList, {});
    const html = React.renderToString(rendered);
    
    return assertContains(html, 'Learn React', 'TodoList renders todos') &&
           assertContains(html, 'Build app', 'TodoList renders all items');
}, 'TodoList component');

// Test 20: Real-world example - Form component
runTest(() => {
    function Form() {
        const [name, setName] = React.useState('');
        const [email, setEmail] = React.useState('');
        
        return React.createElement('form', null,
            React.createElement('input', { 
                type: 'text', 
                value: name,
                placeholder: 'Name'
            }),
            React.createElement('input', { 
                type: 'email', 
                value: email,
                placeholder: 'Email'
            }),
            React.createElement('button', { type: 'submit' }, 'Submit')
        );
    }
    
    const rendered = React.renderComponent(Form, {});
    const html = React.renderToString(rendered);
    
    return assertContains(html, '<form>', 'Form component renders form') &&
           assertContains(html, 'placeholder="Name"', 'Form includes input fields');
}, 'Form component');

// Summary
console.log('\n=== Test Results ===');
console.log(`Total: ${totalTests}`);
console.log(`Passed: ${passedTests}`);
console.log(`Failed: ${totalTests - passedTests}`);
console.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n`);

if (passedTests === totalTests) {
    console.log('✓ All tests passed!');
    process.exit(0);
} else {
    console.log(`✗ ${totalTests - passedTests} test(s) failed.`);
    process.exit(1);
}
