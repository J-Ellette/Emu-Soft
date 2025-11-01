# React Emulator - Frontend Library for JavaScript

**Developed by PowerShield, as an alternative to React**


This module emulates the **React** library, which is a JavaScript library for building user interfaces. React makes it painless to create interactive UIs with a component-based architecture.

## What is React?

React is a JavaScript library developed by Facebook for building user interfaces. It is designed to:
- Build encapsulated components that manage their own state
- Compose components to make complex UIs
- Use a declarative approach to UI development
- Efficiently update and render components with a Virtual DOM
- Support both client and server-side rendering

## Features

This emulator implements core React functionality:

### Components
- **Class Components**: Traditional component class with lifecycle methods
- **Function Components**: Modern stateless functional components
- **Component Composition**: Build complex UIs from simple components

### JSX-like API
- **createElement**: Create virtual DOM elements
- **Fragment**: Group children without extra DOM nodes
- **Props**: Pass data between components
- **Children**: Work with component children

### Hooks (React 16.8+)
- **useState**: Add state to function components
- **useEffect**: Perform side effects
- **useContext**: Subscribe to context
- **useRef**: Create mutable refs
- **useMemo**: Memoize expensive computations
- **useCallback**: Memoize callback functions
- **useReducer**: Manage complex state with reducers

### Context API
- **createContext**: Create context for sharing data
- **Provider**: Provide context value to children
- **Consumer**: Consume context value

### Utilities
- **createRef**: Create refs for DOM access
- **forwardRef**: Forward refs to child components
- **memo**: Optimize components with memoization
- **Children**: Utilities for working with children
- **cloneElement**: Clone and modify elements
- **isValidElement**: Check if value is a React element

## Usage Examples

### Basic Component (Class)

```javascript
const React = require('./react_emulator');

class Welcome extends React.Component {
    render() {
        return React.createElement('h1', null, `Hello, ${this.props.name}`);
    }
}

// Render the component
const element = React.renderComponent(Welcome, { name: 'World' });
const html = React.renderToString(element);
console.log(html); // <h1>Hello, World</h1>
```

### Function Component

```javascript
const React = require('./react_emulator');

function Greeting({ name }) {
    return React.createElement('h1', null, `Hello, ${name}!`);
}

const element = React.renderComponent(Greeting, { name: 'Alice' });
const html = React.renderToString(element);
console.log(html); // <h1>Hello, Alice!</h1>
```

### createElement API

```javascript
const React = require('./react_emulator');

// Simple element
const div = React.createElement('div', { id: 'container' }, 'Hello World');

// Nested elements
const nested = React.createElement('div', { className: 'wrapper' },
    React.createElement('h1', null, 'Title'),
    React.createElement('p', null, 'Paragraph')
);

// With multiple children
const list = React.createElement('ul', null,
    React.createElement('li', null, 'Item 1'),
    React.createElement('li', null, 'Item 2'),
    React.createElement('li', null, 'Item 3')
);
```

### useState Hook

```javascript
const React = require('./react_emulator');

function Counter() {
    const [count, setCount] = React.useState(0);
    
    return React.createElement('div', null,
        React.createElement('p', null, `Count: ${count}`),
        React.createElement('button', { 
            onClick: () => setCount(count + 1) 
        }, 'Increment')
    );
}

const element = React.renderComponent(Counter, {});
```

### useState with Function Initializer

```javascript
const React = require('./react_emulator');

function ExpensiveComponent() {
    // Only runs once during initialization
    const [data, setData] = React.useState(() => {
        // Expensive computation
        return computeExpensiveValue();
    });
    
    return React.createElement('div', null, JSON.stringify(data));
}
```

### useEffect Hook

```javascript
const React = require('./react_emulator');

function DataFetcher({ userId }) {
    const [user, setUser] = React.useState(null);
    
    React.useEffect(() => {
        // Effect runs when userId changes
        fetchUser(userId).then(data => setUser(data));
        
        // Optional cleanup function
        return () => {
            // Cleanup when component unmounts or before next effect
            cancelFetch();
        };
    }, [userId]); // Dependencies array
    
    return React.createElement('div', null, user ? user.name : 'Loading...');
}
```

### useContext Hook

```javascript
const React = require('./react_emulator');

// Create context
const ThemeContext = React.createContext('light');

function ThemedButton() {
    const theme = React.useContext(ThemeContext);
    
    return React.createElement('button', { 
        className: `btn-${theme}` 
    }, 'Click me');
}

// Use the Provider to pass value down
function App() {
    return React.createElement(ThemeContext.Provider, { value: 'dark' },
        React.createElement(ThemedButton, null)
    );
}
```

### useRef Hook

```javascript
const React = require('./react_emulator');

function TextInput() {
    const inputRef = React.useRef(null);
    
    function focusInput() {
        // Access DOM node
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }
    
    return React.createElement('div', null,
        React.createElement('input', { ref: inputRef, type: 'text' }),
        React.createElement('button', { onClick: focusInput }, 'Focus Input')
    );
}
```

### useMemo Hook

```javascript
const React = require('./react_emulator');

function ExpensiveList({ items, filter }) {
    // Only recompute when items or filter changes
    const filteredItems = React.useMemo(() => {
        console.log('Filtering items...');
        return items.filter(item => item.includes(filter));
    }, [items, filter]);
    
    return React.createElement('ul', null,
        filteredItems.map((item, i) => 
            React.createElement('li', { key: i }, item)
        )
    );
}
```

### useCallback Hook

```javascript
const React = require('./react_emulator');

function Parent() {
    const [count, setCount] = React.useState(0);
    
    // Memoize callback - only recreate when count changes
    const handleClick = React.useCallback(() => {
        setCount(count + 1);
    }, [count]);
    
    return React.createElement('div', null,
        React.createElement(Child, { onClick: handleClick }),
        React.createElement('p', null, `Count: ${count}`)
    );
}

function Child({ onClick }) {
    return React.createElement('button', { onClick }, 'Increment');
}
```

### useReducer Hook

```javascript
const React = require('./react_emulator');

function reducer(state, action) {
    switch (action.type) {
        case 'increment':
            return { count: state.count + 1 };
        case 'decrement':
            return { count: state.count - 1 };
        case 'reset':
            return { count: 0 };
        default:
            throw new Error('Unknown action type');
    }
}

function Counter() {
    const [state, dispatch] = React.useReducer(reducer, { count: 0 });
    
    return React.createElement('div', null,
        React.createElement('p', null, `Count: ${state.count}`),
        React.createElement('button', { 
            onClick: () => dispatch({ type: 'increment' }) 
        }, '+'),
        React.createElement('button', { 
            onClick: () => dispatch({ type: 'decrement' }) 
        }, '-'),
        React.createElement('button', { 
            onClick: () => dispatch({ type: 'reset' }) 
        }, 'Reset')
    );
}
```

### createRef

```javascript
const React = require('./react_emulator');

class TextInput extends React.Component {
    constructor(props) {
        super(props);
        this.inputRef = React.createRef();
    }
    
    focusInput() {
        this.inputRef.current.focus();
    }
    
    render() {
        return React.createElement('input', { 
            ref: this.inputRef, 
            type: 'text' 
        });
    }
}
```

### Fragment

```javascript
const React = require('./react_emulator');

function List() {
    return React.createElement(React.Fragment, null,
        React.createElement('li', null, 'Item 1'),
        React.createElement('li', null, 'Item 2'),
        React.createElement('li', null, 'Item 3')
    );
}
```

### memo HOC

```javascript
const React = require('./react_emulator');

// Component only re-renders if props change
const ExpensiveComponent = React.memo(function({ data }) {
    // Expensive rendering logic
    return React.createElement('div', null, JSON.stringify(data));
});

// Custom comparison function
const CustomMemo = React.memo(
    function({ value }) {
        return React.createElement('div', null, value);
    },
    (prevProps, nextProps) => {
        // Return true if props are equal (skip re-render)
        return prevProps.value === nextProps.value;
    }
);
```

### Children Utilities

```javascript
const React = require('./react_emulator');

function Container({ children }) {
    // Map over children
    const enhanced = React.Children.map(children, (child, index) => {
        return React.cloneElement(child, { key: index });
    });
    
    // Count children
    const count = React.Children.count(children);
    
    // Convert to array
    const childArray = React.Children.toArray(children);
    
    return React.createElement('div', null, enhanced);
}
```

### forwardRef

```javascript
const React = require('./react_emulator');

const FancyInput = React.forwardRef((props, ref) => {
    return React.createElement('input', {
        ...props,
        ref: ref,
        className: 'fancy-input'
    });
});

function Parent() {
    const inputRef = React.useRef(null);
    
    return React.createElement(FancyInput, { ref: inputRef });
}
```

### Component Lifecycle (Class Component)

```javascript
const React = require('./react_emulator');

class LifecycleComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = { data: null };
    }
    
    componentDidMount() {
        // Called after component is mounted
        console.log('Component mounted');
        this.fetchData();
    }
    
    componentDidUpdate(prevProps, prevState) {
        // Called after component updates
        if (prevProps.userId !== this.props.userId) {
            this.fetchData();
        }
    }
    
    componentWillUnmount() {
        // Called before component is unmounted
        console.log('Component will unmount');
        this.cancelFetch();
    }
    
    shouldComponentUpdate(nextProps, nextState) {
        // Control whether component should update
        return nextState.data !== this.state.data;
    }
    
    fetchData() {
        // Fetch data
    }
    
    cancelFetch() {
        // Cancel pending requests
    }
    
    render() {
        return React.createElement('div', null, this.state.data);
    }
}
```

### Real-World Example: Todo App

```javascript
const React = require('./react_emulator');

function TodoApp() {
    const [todos, setTodos] = React.useState([]);
    const [input, setInput] = React.useState('');
    
    function addTodo() {
        if (input.trim()) {
            setTodos([...todos, { id: Date.now(), text: input, completed: false }]);
            setInput('');
        }
    }
    
    function toggleTodo(id) {
        setTodos(todos.map(todo =>
            todo.id === id ? { ...todo, completed: !todo.completed } : todo
        ));
    }
    
    function deleteTodo(id) {
        setTodos(todos.filter(todo => todo.id !== id));
    }
    
    return React.createElement('div', { className: 'todo-app' },
        React.createElement('h1', null, 'Todo List'),
        React.createElement('div', { className: 'input-group' },
            React.createElement('input', {
                type: 'text',
                value: input,
                onChange: (e) => setInput(e.target.value),
                placeholder: 'Add a todo...'
            }),
            React.createElement('button', { onClick: addTodo }, 'Add')
        ),
        React.createElement('ul', { className: 'todo-list' },
            todos.map(todo =>
                React.createElement('li', { 
                    key: todo.id,
                    className: todo.completed ? 'completed' : ''
                },
                    React.createElement('input', {
                        type: 'checkbox',
                        checked: todo.completed,
                        onChange: () => toggleTodo(todo.id)
                    }),
                    React.createElement('span', null, todo.text),
                    React.createElement('button', {
                        onClick: () => deleteTodo(todo.id)
                    }, 'Delete')
                )
            )
        )
    );
}
```

### Real-World Example: User Profile

```javascript
const React = require('./react_emulator');

function UserProfile({ userId }) {
    const [user, setUser] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    
    React.useEffect(() => {
        setLoading(true);
        setError(null);
        
        fetch(`/api/users/${userId}`)
            .then(response => response.json())
            .then(data => {
                setUser(data);
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, [userId]);
    
    if (loading) {
        return React.createElement('div', null, 'Loading...');
    }
    
    if (error) {
        return React.createElement('div', { className: 'error' }, error);
    }
    
    return React.createElement('div', { className: 'user-profile' },
        React.createElement('img', { src: user.avatar, alt: user.name }),
        React.createElement('h2', null, user.name),
        React.createElement('p', null, user.bio),
        React.createElement('div', { className: 'stats' },
            React.createElement('span', null, `Followers: ${user.followers}`),
            React.createElement('span', null, `Following: ${user.following}`)
        )
    );
}
```

### Real-World Example: Form Validation

```javascript
const React = require('./react_emulator');

function SignupForm() {
    const [formData, setFormData] = React.useState({
        username: '',
        email: '',
        password: ''
    });
    const [errors, setErrors] = React.useState({});
    
    function handleChange(field, value) {
        setFormData({ ...formData, [field]: value });
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors({ ...errors, [field]: null });
        }
    }
    
    function validate() {
        const newErrors = {};
        
        if (!formData.username) {
            newErrors.username = 'Username is required';
        }
        
        if (!formData.email || !formData.email.includes('@')) {
            newErrors.email = 'Valid email is required';
        }
        
        if (formData.password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters';
        }
        
        return newErrors;
    }
    
    function handleSubmit(e) {
        e.preventDefault();
        
        const newErrors = validate();
        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }
        
        // Submit form
        console.log('Form submitted:', formData);
    }
    
    return React.createElement('form', { onSubmit: handleSubmit },
        React.createElement('h2', null, 'Sign Up'),
        
        React.createElement('div', { className: 'form-group' },
            React.createElement('label', null, 'Username'),
            React.createElement('input', {
                type: 'text',
                value: formData.username,
                onChange: (e) => handleChange('username', e.target.value)
            }),
            errors.username && React.createElement('span', { className: 'error' }, errors.username)
        ),
        
        React.createElement('div', { className: 'form-group' },
            React.createElement('label', null, 'Email'),
            React.createElement('input', {
                type: 'email',
                value: formData.email,
                onChange: (e) => handleChange('email', e.target.value)
            }),
            errors.email && React.createElement('span', { className: 'error' }, errors.email)
        ),
        
        React.createElement('div', { className: 'form-group' },
            React.createElement('label', null, 'Password'),
            React.createElement('input', {
                type: 'password',
                value: formData.password,
                onChange: (e) => handleChange('password', e.target.value)
            }),
            errors.password && React.createElement('span', { className: 'error' }, errors.password)
        ),
        
        React.createElement('button', { type: 'submit' }, 'Sign Up')
    );
}
```

## Testing

Run the comprehensive test suite:

```bash
node test_react_emulator.js
```

Tests cover:
- createElement (4 tests)
- Component class (2 tests)
- Function components (1 test)
- useState hook (2 tests)
- useEffect hook (1 test)
- useRef hook (1 test)
- useMemo hook (1 test)
- useCallback hook (1 test)
- useReducer hook (1 test)
- Context API (2 tests)
- Refs (2 tests)
- Fragment (1 test)
- Children utilities (3 tests)
- cloneElement (1 test)
- isValidElement (2 tests)
- renderToString (3 tests)
- memo (1 test)
- Real-world examples (3 tests)

Total: 28 tests

## Integration with Existing Code

This emulator is designed to be a drop-in replacement for React in development and testing:

```javascript
// Instead of:
// const React = require('react');

// Use:
const React = require('./react_emulator');

// The rest of your code remains unchanged
function App() {
    return React.createElement('div', null, 'Hello World');
}
```

## Use Cases

Perfect for:
- **Local Development**: Develop React apps without npm dependencies
- **Testing**: Test React components in isolation
- **Learning**: Understand how React works internally
- **Education**: Teach React concepts and patterns
- **Prototyping**: Quickly prototype React applications
- **Server-Side**: Simple server-side rendering

## Limitations

This is an emulator for development and testing purposes:
- No actual DOM manipulation
- No event system (events are just props)
- Simplified hooks implementation
- No reconciliation algorithm
- No Fiber architecture
- No concurrent rendering
- No Suspense or Error Boundaries
- No portals
- No strict mode
- Limited lifecycle methods
- Simplified renderToString

## Supported Features

### Core
- ✅ createElement
- ✅ Component (class)
- ✅ Function components
- ✅ Fragment
- ✅ Props
- ✅ State (setState)

### Hooks
- ✅ useState
- ✅ useEffect
- ✅ useContext
- ✅ useRef
- ✅ useMemo
- ✅ useCallback
- ✅ useReducer

### Context
- ✅ createContext
- ✅ Provider
- ✅ Consumer
- ✅ useContext

### Refs
- ✅ createRef
- ✅ forwardRef
- ✅ useRef

### Performance
- ✅ memo

### Utilities
- ✅ Children (map, forEach, count, only, toArray)
- ✅ cloneElement
- ✅ isValidElement

### Lifecycle (Class Components)
- ✅ componentDidMount
- ✅ componentDidUpdate
- ✅ componentWillUnmount
- ✅ shouldComponentUpdate

### Rendering
- ✅ renderComponent (simplified)
- ✅ renderToString (simplified SSR)

## Real-World React Concepts

This emulator teaches the following concepts:

1. **Component-Based Architecture**: Building UIs from reusable components
2. **Declarative UI**: Describing what the UI should look like
3. **State Management**: Managing component state with useState/setState
4. **Side Effects**: Handling side effects with useEffect
5. **Composition**: Combining components to build complex UIs
6. **Props**: Passing data between components
7. **Hooks**: Using hooks for state and side effects in function components
8. **Context**: Sharing data across component tree
9. **Refs**: Accessing DOM nodes and persisting values
10. **Memoization**: Optimizing performance with memo, useMemo, useCallback
11. **Lifecycle**: Understanding component lifecycle
12. **Virtual DOM**: Understanding how React represents UI

## Compatibility

Emulates core features of:
- React 16.8+ (Hooks era)
- Common React patterns and practices
- React API conventions

## License

Part of the Emu-Soft project. See main repository LICENSE.
