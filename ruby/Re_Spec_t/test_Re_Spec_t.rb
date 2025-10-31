#!/usr/bin/env ruby
require_relative 'Re_Spec_t'

describe 'Basic Math' do
  it 'adds two numbers' do
    expect(2 + 2).to eq(4)
  end
  
  it 'subtracts two numbers' do
    expect(5 - 3).to eq(2)
  end
  
  it 'multiplies two numbers' do
    expect(3 * 4).to eq(12)
  end
end

describe 'String operations' do
  context 'when empty' do
    it 'has zero length' do
      expect("".length).to eq(0)
    end
    
    it 'is empty' do
      expect("".empty?).to be_truthy
    end
  end
  
  context 'when not empty' do
    it 'has non-zero length' do
      expect("hello".length).to be_greater_than(0)
    end
    
    it 'can be concatenated' do
      expect("hello" + " world").to eq("hello world")
    end
  end
end

describe 'Array operations' do
  let(:array) { [1, 2, 3, 4, 5] }
  
  it 'has correct length' do
    expect(array.length).to eq(5)
  end
  
  it 'includes specific values' do
    expect(array).to include(3)
  end
  
  it 'can be mapped' do
    result = array.map { |x| x * 2 }
    expect(result).to eq([2, 4, 6, 8, 10])
  end
end

describe 'Nil and boolean checks' do
  it 'checks for nil' do
    expect(nil).to be_nil
    expect("value").not_to be_nil
  end
  
  it 'checks truthiness' do
    expect(true).to be_truthy
    expect(1).to be_truthy
    expect("hello").to be_truthy
  end
  
  it 'checks falsiness' do
    expect(false).to be_falsey
    expect(nil).to be_falsey
  end
end

describe 'Exception handling' do
  it 'raises runtime error' do
    block = lambda { raise "Error" }
    expect(block).to raise_error(RuntimeError)
  end
end

describe 'Hash operations' do
  subject { { name: 'Alice', age: 30 } }
  
  it 'has keys' do
    expect(subject.keys).to include(:name)
  end
  
  it 'has values' do
    expect(subject.values).to include(30)
  end
  
  it 'can be accessed' do
    expect(subject[:name]).to eq('Alice')
  end
end

describe 'Hooks' do
  before do
    @setup_value = 42
  end
  
  it 'uses before hook' do
    expect(@setup_value).to eq(42)
  end
  
  it 'before hook runs for each test' do
    @setup_value = 100
    expect(@setup_value).to eq(100)
  end
end

describe 'Comparisons' do
  it 'compares greater than' do
    expect(10).to be_greater_than(5)
  end
  
  it 'compares less than' do
    expect(3).to be_less_than(10)
  end
end

run_specs
