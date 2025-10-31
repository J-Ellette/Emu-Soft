/**
 * React Emulator - Frontend Library for JavaScript
 * 
 * This module emulates the React library, which is a JavaScript library for
 * building user interfaces. React makes it painless to create interactive UIs
 * with a component-based architecture.
 * 
 * Key Features:
 * - Component creation (function and class components)
 * - Virtual DOM representation
 * - JSX-like element creation
 * - State management with hooks
 * - Lifecycle methods
 * - Props handling
 * - Event handling
 */

/**
 * Element type symbol
 */
const REACT_ELEMENT_TYPE = Symbol.for('react.element');

/**
 * Create a React element (Virtual DOM node)
 */
function createElement(type, props = null, ...children) {
    const element = {
        $$typeof: REACT_ELEMENT_TYPE,
        type,
        props: {
            ...(props || {}),
            children: children.length === 1 ? children[0] : children
        },
        key: props?.key || null,
        ref: props?.ref || null
    };
    
    // Remove key and ref from props
    if (element.props.key !== undefined) delete element.props.key;
    if (element.props.ref !== undefined) delete element.props.ref;
    
    return element;
}

/**
 * Component base class
 */
class Component {
    constructor(props = {}) {
        this.props = props;
        this.state = {};
        this._isMounted = false;
    }

    setState(partialState, callback) {
        if (typeof partialState === 'function') {
            partialState = partialState(this.state, this.props);
        }
        
        this.state = {
            ...this.state,
            ...partialState
        };
        
        // Trigger re-render (simplified)
        if (this._isMounted && this.forceUpdate) {
            this.forceUpdate();
        }
        
        if (callback) {
            callback();
        }
    }

    forceUpdate() {
        // Simplified force update - in real React this would re-render
        if (this.componentDidUpdate) {
            this.componentDidUpdate(this.props, this.state);
        }
    }

    // Lifecycle methods (to be overridden)
    componentDidMount() {}
    componentDidUpdate(prevProps, prevState) {}
    componentWillUnmount() {}
    shouldComponentUpdate(nextProps, nextState) {
        return true;
    }
}

/**
 * Hooks state management
 */
let currentComponent = null;
let currentHookIndex = 0;
let hookStates = new WeakMap();

function getHookState(component) {
    if (!hookStates.has(component)) {
        hookStates.set(component, []);
    }
    return hookStates.get(component);
}

/**
 * useState hook
 */
function useState(initialValue) {
    if (!currentComponent) {
        throw new Error('Hooks can only be called inside function components');
    }
    
    const component = currentComponent;
    const hookIndex = currentHookIndex++;
    const hooks = getHookState(component);
    
    // Initialize state if not exists
    if (hooks[hookIndex] === undefined) {
        hooks[hookIndex] = {
            state: typeof initialValue === 'function' ? initialValue() : initialValue
        };
    }
    
    const hook = hooks[hookIndex];
    
    const setState = (newValue) => {
        const value = typeof newValue === 'function' 
            ? newValue(hook.state) 
            : newValue;
        
        hook.state = value;
        
        // Trigger re-render (simplified)
        if (component._forceUpdate) {
            component._forceUpdate();
        }
    };
    
    return [hook.state, setState];
}

/**
 * useEffect hook
 */
function useEffect(effect, dependencies) {
    if (!currentComponent) {
        throw new Error('Hooks can only be called inside function components');
    }
    
    const component = currentComponent;
    const hookIndex = currentHookIndex++;
    const hooks = getHookState(component);
    
    const prevEffect = hooks[hookIndex];
    
    // Check if dependencies changed
    const hasChanged = !prevEffect || 
        !dependencies || 
        !prevEffect.dependencies ||
        dependencies.some((dep, i) => dep !== prevEffect.dependencies[i]);
    
    if (hasChanged) {
        // Clean up previous effect
        if (prevEffect && prevEffect.cleanup) {
            prevEffect.cleanup();
        }
        
        // Run new effect
        const cleanup = effect();
        
        hooks[hookIndex] = {
            dependencies: dependencies ? [...dependencies] : null,
            cleanup
        };
    }
}

/**
 * useContext hook
 */
function useContext(context) {
    if (!currentComponent) {
        throw new Error('Hooks can only be called inside function components');
    }
    return context._currentValue;
}

/**
 * useRef hook
 */
function useRef(initialValue) {
    if (!currentComponent) {
        throw new Error('Hooks can only be called inside function components');
    }
    
    const component = currentComponent;
    const hookIndex = currentHookIndex++;
    const hooks = getHookState(component);
    
    if (hooks[hookIndex] === undefined) {
        hooks[hookIndex] = {
            current: initialValue
        };
    }
    
    return hooks[hookIndex];
}

/**
 * useMemo hook
 */
function useMemo(factory, dependencies) {
    if (!currentComponent) {
        throw new Error('Hooks can only be called inside function components');
    }
    
    const component = currentComponent;
    const hookIndex = currentHookIndex++;
    const hooks = getHookState(component);
    
    const prevMemo = hooks[hookIndex];
    
    // Check if dependencies changed
    const hasChanged = !prevMemo || 
        !dependencies || 
        !prevMemo.dependencies ||
        dependencies.some((dep, i) => dep !== prevMemo.dependencies[i]);
    
    if (hasChanged) {
        const value = factory();
        hooks[hookIndex] = {
            value,
            dependencies: dependencies ? [...dependencies] : null
        };
        return value;
    }
    
    return prevMemo.value;
}

/**
 * useCallback hook
 */
function useCallback(callback, dependencies) {
    return useMemo(() => callback, dependencies);
}

/**
 * useReducer hook
 */
function useReducer(reducer, initialState, init) {
    const [state, setState] = useState(
        init ? init(initialState) : initialState
    );
    
    const dispatch = (action) => {
        const newState = reducer(state, action);
        setState(newState);
    };
    
    return [state, dispatch];
}

/**
 * Create context
 */
function createContext(defaultValue) {
    const context = {
        _currentValue: defaultValue,
        Provider: function({ value, children }) {
            context._currentValue = value;
            return children;
        },
        Consumer: function({ children }) {
            return children(context._currentValue);
        }
    };
    return context;
}

/**
 * Render a component (simplified)
 */
function renderComponent(Component, props = {}) {
    currentHookIndex = 0;
    
    if (typeof Component === 'function') {
        // Check if it's a class component
        if (Component.prototype?.isReactComponent) {
            const instance = new Component(props);
            instance._isMounted = true;
            
            if (instance.componentDidMount) {
                instance.componentDidMount();
            }
            
            return instance.render();
        } else {
            // Function component
            const componentInstance = { _forceUpdate: null };
            currentComponent = componentInstance;
            const result = Component(props);
            currentComponent = null;
            return result;
        }
    } else if (typeof Component === 'string') {
        // HTML element
        return createElement(Component, props);
    }
    
    return Component;
}

/**
 * Render element to string (simplified)
 */
function renderToString(element) {
    if (element === null || element === undefined) {
        return '';
    }
    
    if (typeof element === 'string' || typeof element === 'number') {
        return String(element);
    }
    
    if (Array.isArray(element)) {
        return element.map(renderToString).join('');
    }
    
    if (element.$$typeof === REACT_ELEMENT_TYPE) {
        const { type, props } = element;
        
        if (typeof type === 'string') {
            // HTML element
            const attrs = Object.keys(props)
                .filter(key => key !== 'children' && props[key] !== undefined)
                .map(key => {
                    if (key === 'className') return `class="${props[key]}"`;
                    if (key === 'htmlFor') return `for="${props[key]}"`;
                    return `${key}="${props[key]}"`;
                })
                .join(' ');
            
            const attrsStr = attrs ? ' ' + attrs : '';
            
            // Self-closing tags
            if (['img', 'br', 'hr', 'input', 'meta', 'link'].includes(type)) {
                return `<${type}${attrsStr} />`;
            }
            
            const children = props.children;
            const childrenStr = renderToString(children);
            
            return `<${type}${attrsStr}>${childrenStr}</${type}>`;
        } else if (typeof type === 'function') {
            // Component
            const rendered = renderComponent(type, props);
            return renderToString(rendered);
        }
    }
    
    return '';
}

/**
 * Fragment component
 */
const Fragment = ({ children }) => children;

/**
 * Create ref
 */
function createRef() {
    return {
        current: null
    };
}

/**
 * Forward ref
 */
function forwardRef(render) {
    return function ForwardRef(props) {
        return render(props, props.ref);
    };
}

/**
 * Memo HOC for performance optimization
 */
function memo(Component, areEqual) {
    const MemoizedComponent = function(props) {
        return Component(props);
    };
    
    MemoizedComponent._isMemoized = true;
    MemoizedComponent._areEqual = areEqual;
    
    return MemoizedComponent;
}

/**
 * Children utilities
 */
const Children = {
    map(children, fn) {
        if (!children) return [];
        return Array.isArray(children) 
            ? children.map(fn) 
            : [fn(children, 0)];
    },
    
    forEach(children, fn) {
        if (!children) return;
        if (Array.isArray(children)) {
            children.forEach(fn);
        } else {
            fn(children, 0);
        }
    },
    
    count(children) {
        if (!children) return 0;
        return Array.isArray(children) ? children.length : 1;
    },
    
    only(children) {
        if (Array.isArray(children) && children.length === 1) {
            return children[0];
        }
        if (!Array.isArray(children)) {
            return children;
        }
        throw new Error('Children.only expected to receive a single child');
    },
    
    toArray(children) {
        if (!children) return [];
        return Array.isArray(children) ? children : [children];
    }
};

/**
 * Clone element
 */
function cloneElement(element, props, ...children) {
    return {
        ...element,
        props: {
            ...element.props,
            ...props,
            children: children.length > 0 ? children : element.props.children
        }
    };
}

/**
 * isValidElement
 */
function isValidElement(object) {
    return (
        typeof object === 'object' &&
        object !== null &&
        object.$$typeof === REACT_ELEMENT_TYPE
    );
}

// Mark Component as React component
Component.prototype.isReactComponent = true;

// Export React API
module.exports = {
    // Core
    createElement,
    Component,
    Fragment,
    
    // Hooks
    useState,
    useEffect,
    useContext,
    useRef,
    useMemo,
    useCallback,
    useReducer,
    
    // Context
    createContext,
    
    // Refs
    createRef,
    forwardRef,
    
    // Performance
    memo,
    
    // Utilities
    Children,
    cloneElement,
    isValidElement,
    
    // Rendering (for testing)
    renderComponent,
    renderToString,
    
    // Internal
    REACT_ELEMENT_TYPE
};
