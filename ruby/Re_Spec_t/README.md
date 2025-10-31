# RSpec Testing Framework Emulator

A lightweight emulation of **RSpec**, the popular behavior-driven development (BDD) testing framework for Ruby.

## Features

This emulator implements core RSpec functionality:

### Test Structure
- **describe**: Define test suites
- **context**: Group related tests
- **it/specify**: Define test cases
- **Example Groups**: Organize tests hierarchically

### Expectations
- **expect**: Set up expectations
- **to/not_to**: Match expectations
- **Matchers**: Built-in matcher library

### Matchers
- **eq**: Equality matcher
- **be_nil**: Nil matcher
- **be_truthy/be_falsey**: Boolean matchers
- **include**: Collection inclusion
- **raise_error**: Exception matching
- **be_greater_than/be_less_than**: Comparison matchers

### Hooks
- **before**: Run code before examples
- **after**: Run code after examples
- **let**: Define memoized helper methods
- **subject**: Define the test subject

### Test Execution
- **Runner**: Execute test suites
- **Formatting**: Documentation-style output
- **Summary**: Test results summary
- **Pass/Fail Tracking**: Count successes and failures

## What It Emulates

This tool emulates [RSpec](https://rspec.info/), the most popular testing framework in the Ruby ecosystem, used by Rails and thousands of Ruby projects.

### Core Components Implemented

1. **DSL (Domain Specific Language)**
   - describe/context blocks
   - it/specify examples
   - expect syntax

2. **Matchers**
   - Equality matchers
   - Boolean matchers
   - Collection matchers
   - Exception matchers

3. **Hooks**
   - before/after hooks
   - let/subject helpers

4. **Runner**
   - Example execution
   - Result reporting
   - Summary statistics

## Usage

### Basic Test Structure

```ruby
require_relative 'rspec_emulator'

describe 'Calculator' do
  it 'adds two numbers' do
    result = 2 + 2
    expect(result).to eq(4)
  end
  
  it 'subtracts two numbers' do
    result = 5 - 3
    expect(result).to eq(2)
  end
end

run_specs
```

### Using Context

```ruby
describe 'String' do
  context 'when empty' do
    it 'has zero length' do
      str = ""
      expect(str.length).to eq(0)
    end
    
    it 'is empty' do
      str = ""
      expect(str.empty?).to be_truthy
    end
  end
  
  context 'when not empty' do
    it 'has non-zero length' do
      str = "hello"
      expect(str.length).to be_greater_than(0)
    end
  end
end
```

### Expectations and Matchers

```ruby
describe 'Matchers' do
  it 'tests equality' do
    expect(2 + 2).to eq(4)
    expect("hello").to eq("hello")
  end
  
  it 'tests nil' do
    expect(nil).to be_nil
    expect("value").not_to be_nil
  end
  
  it 'tests truthiness' do
    expect(true).to be_truthy
    expect(1).to be_truthy
    expect(false).to be_falsey
    expect(nil).to be_falsey
  end
  
  it 'tests inclusion' do
    expect([1, 2, 3]).to include(2)
    expect("hello world").to include("world")
  end
  
  it 'tests exceptions' do
    expect { raise StandardError }.to raise_error(StandardError)
  end
  
  it 'tests comparisons' do
    expect(10).to be_greater_than(5)
    expect(3).to be_less_than(10)
  end
end
```

### Hooks and Setup

```ruby
describe 'Array' do
  before do
    @array = [1, 2, 3, 4, 5]
  end
  
  after do
    @array = nil
  end
  
  it 'has correct length' do
    expect(@array.length).to eq(5)
  end
  
  it 'includes specific values' do
    expect(@array).to include(3)
  end
end
```

### Let and Subject

```ruby
describe 'User' do
  let(:user) { { name: 'John', age: 30 } }
  
  it 'has a name' do
    expect(user[:name]).to eq('John')
  end
  
  it 'has an age' do
    expect(user[:age]).to eq(30)
  end
end

describe 'Hash' do
  subject { { a: 1, b: 2 } }
  
  it 'has keys' do
    expect(subject.keys).to include(:a)
  end
  
  it 'has values' do
    expect(subject.values).to include(1)
  end
end
```

### Complete Example

```ruby
require_relative 'rspec_emulator'

describe 'BankAccount' do
  let(:account) { { balance: 100, transactions: [] } }
  
  before do
    puts "Setting up test"
  end
  
  context 'when depositing money' do
    it 'increases the balance' do
      account[:balance] += 50
      expect(account[:balance]).to eq(150)
    end
    
    it 'records the transaction' do
      account[:transactions] << { type: :deposit, amount: 50 }
      expect(account[:transactions].length).to eq(1)
    end
  end
  
  context 'when withdrawing money' do
    it 'decreases the balance' do
      account[:balance] -= 30
      expect(account[:balance]).to eq(70)
    end
    
    it 'does not allow overdraft' do
      account[:balance] = 10
      expect { 
        raise "Insufficient funds" if account[:balance] < 50
        account[:balance] -= 50
      }.to raise_error(RuntimeError)
    end
  end
  
  context 'balance checks' do
    it 'is positive when funded' do
      expect(account[:balance]).to be_greater_than(0)
    end
    
    it 'has transactions array' do
      expect(account[:transactions]).not_to be_nil
    end
  end
end

run_specs
```

### Testing Classes

```ruby
class Calculator
  def add(a, b)
    a + b
  end
  
  def divide(a, b)
    raise ZeroDivisionError if b == 0
    a / b
  end
end

describe Calculator do
  let(:calc) { Calculator.new }
  
  describe '#add' do
    it 'adds two positive numbers' do
      expect(calc.add(2, 3)).to eq(5)
    end
    
    it 'adds negative numbers' do
      expect(calc.add(-2, -3)).to eq(-5)
    end
  end
  
  describe '#divide' do
    it 'divides two numbers' do
      expect(calc.divide(10, 2)).to eq(5)
    end
    
    it 'raises error when dividing by zero' do
      expect { calc.divide(10, 0) }.to raise_error(ZeroDivisionError)
    end
  end
end
```

## Testing

```bash
ruby test_rspec_emulator.rb
```

## Use Cases

1. **Learning RSpec**: Understand RSpec concepts
2. **Test Development**: Write behavior-driven tests
3. **Education**: Teaching testing practices
4. **TDD/BDD**: Test-driven and behavior-driven development
5. **Documentation**: Executable specifications
6. **Code Quality**: Ensure code correctness

## Key Differences from Real RSpec

1. **Limited Matchers**: Only basic matchers implemented
2. **No Mocking**: Test doubles and mocks not included
3. **Simplified Hooks**: Only basic before/after hooks
4. **No Shared Examples**: Shared example groups not supported
5. **Basic Formatting**: Simple output formatting only
6. **No Configuration Options**: Limited configuration
7. **No Filtering**: Can't filter tests by tag
8. **No Parallel Execution**: Tests run sequentially
9. **No Custom Matchers**: Can't define custom matchers easily
10. **No Metadata**: Example metadata not supported

## RSpec Concepts

### BDD (Behavior-Driven Development)
RSpec encourages writing tests that describe behavior rather than implementation details.

### Example Groups
Organized using `describe` and `context` blocks to group related tests.

### Examples
Individual test cases defined with `it` or `specify`.

### Expectations
Assertions about code behavior using `expect(...).to` syntax.

### Matchers
Methods that check if expectations are met (eq, be_nil, include, etc.).

### Hooks
Code that runs before or after examples for setup and teardown.

### Let
Lazy-evaluated helper methods that are memoized per example.

## Best Practices

1. **Descriptive Names**: Use clear descriptions for tests
2. **One Expectation**: Each example should test one thing
3. **Use Context**: Group related scenarios
4. **DRY with Let**: Reduce duplication with let/subject
5. **Hooks for Setup**: Use before hooks for common setup
6. **Test Behavior**: Focus on what code does, not how

## License

Educational emulator for learning purposes.

## References

- [RSpec Documentation](https://rspec.info/documentation/)
- [RSpec Core](https://github.com/rspec/rspec-core)
- [Better Specs](https://www.betterspecs.org/)
- [RSpec Style Guide](https://rspec.rubystyle.guide/)
