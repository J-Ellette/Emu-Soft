// Developed by PowerShield, as an alternative to Tokio

#[path = "tokio_emulator.rs"]
mod tokio_emulator;

use tokio_emulator::*;

struct TestResult {
    name: String,
    passed: bool,
    error: Option<String>,
}

fn test_runner<F>(name: &str, test_fn: F) -> TestResult
where
    F: FnOnce() -> Result<(), String>,
{
    match test_fn() {
        Ok(_) => TestResult {
            name: name.to_string(),
            passed: true,
            error: None,
        },
        Err(e) => TestResult {
            name: name.to_string(),
            passed: false,
            error: Some(e),
        },
    }
}

fn main() {
    println!("Running Tokio Emulator Tests");
    println!("============================\n");
    
    let mut results = Vec::new();
    
    // Test 1: Runtime creation
    results.push(test_runner("Runtime creation", || {
        let _rt = Runtime::new();
        Ok(())
    }));
    
    // Test 2: Task completion
    results.push(test_runner("Task completion", || {
        let mut rt = Runtime::new();
        let mut task = Task::new();
        task.complete(42);
        let result = rt.block_on(task);
        if result == 42 {
            Ok(())
        } else {
            Err(format!("Expected 42, got {}", result))
        }
    }));
    
    // Test 3: Sleep future
    results.push(test_runner("Sleep future", || {
        let mut rt = Runtime::new();
        let sleep = Sleep::new(3);
        rt.block_on(sleep);
        Ok(())
    }));
    
    // Test 4: Task polling - Pending state
    results.push(test_runner("Task polling - Pending", || {
        let mut task: Task<i32> = Task::new();
        match task.poll() {
            Poll::Pending => Ok(()),
            Poll::Ready(_) => Err("Expected Pending, got Ready".to_string()),
        }
    }));
    
    // Test 5: Task polling - Ready state
    results.push(test_runner("Task polling - Ready", || {
        let mut task = Task::new();
        task.complete(100);
        match task.poll() {
            Poll::Ready(value) if value == 100 => Ok(()),
            Poll::Ready(value) => Err(format!("Expected 100, got {}", value)),
            Poll::Pending => Err("Expected Ready, got Pending".to_string()),
        }
    }));
    
    // Test 6: Timeout - Success
    results.push(test_runner("Timeout - Success", || {
        let mut rt = Runtime::new();
        let fast_task = Sleep::new(2);
        let timeout = Timeout::new(fast_task, 5);
        match rt.block_on(timeout) {
            Ok(_) => Ok(()),
            Err(_) => Err("Task should not have timed out".to_string()),
        }
    }));
    
    // Test 7: Timeout - Failure
    results.push(test_runner("Timeout - Failure", || {
        let mut rt = Runtime::new();
        let slow_task = Sleep::new(10);
        let timeout = Timeout::new(slow_task, 3);
        match rt.block_on(timeout) {
            Ok(_) => Err("Task should have timed out".to_string()),
            Err(_) => Ok(()),
        }
    }));
    
    // Test 8: Channel send and receive
    results.push(test_runner("Channel send and receive", || {
        let mut channel: Channel<i32> = Channel::new();
        channel.send(42);
        match channel.try_recv() {
            Some(value) if value == 42 => Ok(()),
            Some(value) => Err(format!("Expected 42, got {}", value)),
            None => Err("Expected value, got None".to_string()),
        }
    }));
    
    // Test 9: Channel empty receive
    results.push(test_runner("Channel empty receive", || {
        let mut channel: Channel<i32> = Channel::new();
        match channel.try_recv() {
            None => Ok(()),
            Some(_) => Err("Expected None, got Some".to_string()),
        }
    }));
    
    // Test 10: Channel multiple messages
    results.push(test_runner("Channel multiple messages", || {
        let mut channel: Channel<String> = Channel::new();
        channel.send("first".to_string());
        channel.send("second".to_string());
        
        let msg1 = channel.try_recv();
        let msg2 = channel.try_recv();
        
        if msg1 == Some("first".to_string()) && msg2 == Some("second".to_string()) {
            Ok(())
        } else {
            Err("Messages not received in correct order".to_string())
        }
    }));
    
    // Test 11: JoinHandle creation
    results.push(test_runner("JoinHandle creation", || {
        let handle = JoinHandle::new(42);
        let result = handle.await_result();
        if result == 42 {
            Ok(())
        } else {
            Err(format!("Expected 42, got {}", result))
        }
    }));
    
    // Test 12: Async function
    results.push(test_runner("Async function", || {
        let mut rt = Runtime::new();
        let async_fn = async_block(|| 100);
        let result = rt.block_on(async_fn);
        if result == 100 {
            Ok(())
        } else {
            Err(format!("Expected 100, got {}", result))
        }
    }));
    
    // Test 13: Yield future - first poll
    results.push(test_runner("Yield future - first poll", || {
        let mut yield_future = Yield::new();
        match yield_future.poll() {
            Poll::Pending => Ok(()),
            Poll::Ready(_) => Err("Expected Pending, got Ready".to_string()),
        }
    }));
    
    // Test 14: Yield future - second poll
    results.push(test_runner("Yield future - second poll", || {
        let mut yield_future = Yield::new();
        yield_future.poll(); // First poll
        match yield_future.poll() {
            Poll::Ready(_) => Ok(()),
            Poll::Pending => Err("Expected Ready, got Pending".to_string()),
        }
    }));
    
    // Test 15: Task is_ready check
    results.push(test_runner("Task is_ready check", || {
        let mut task: Task<i32> = Task::new();
        if task.is_ready() {
            return Err("Task should not be ready".to_string());
        }
        task.complete(42);
        if task.is_ready() {
            Ok(())
        } else {
            Err("Task should be ready".to_string())
        }
    }));
    
    // Test 16: Multiple task completion
    results.push(test_runner("Multiple task completion", || {
        let mut rt = Runtime::new();
        let mut task1 = Task::new();
        let mut task2 = Task::new();
        task1.complete(10);
        task2.complete(20);
        
        let result1 = rt.block_on(task1);
        let result2 = rt.block_on(task2);
        
        if result1 == 10 && result2 == 20 {
            Ok(())
        } else {
            Err(format!("Expected 10 and 20, got {} and {}", result1, result2))
        }
    }));
    
    // Test 17: String task
    results.push(test_runner("String task", || {
        let mut rt = Runtime::new();
        let mut task = Task::new();
        task.complete("Hello".to_string());
        let result = rt.block_on(task);
        if result == "Hello" {
            Ok(())
        } else {
            Err(format!("Expected 'Hello', got '{}'", result))
        }
    }));
    
    // Test 18: Zero-tick sleep
    results.push(test_runner("Zero-tick sleep", || {
        let mut rt = Runtime::new();
        let sleep = Sleep::new(0);
        rt.block_on(sleep);
        Ok(())
    }));
    
    // Test 19: Channel with different types
    results.push(test_runner("Channel with different types", || {
        let mut channel: Channel<bool> = Channel::new();
        channel.send(true);
        channel.send(false);
        
        if channel.try_recv() == Some(true) && channel.try_recv() == Some(false) {
            Ok(())
        } else {
            Err("Channel values incorrect".to_string())
        }
    }));
    
    // Test 20: Async block with side effects
    results.push(test_runner("Async block with side effects", || {
        let mut rt = Runtime::new();
        let mut counter = 0;
        let async_fn = async_block(|| {
            counter += 1;
            counter
        });
        let result = rt.block_on(async_fn);
        if result == 1 {
            Ok(())
        } else {
            Err(format!("Expected 1, got {}", result))
        }
    }));
    
    // Print results
    println!("\n=== Test Results ===");
    let mut passed = 0;
    for result in &results {
        if result.passed {
            println!("✓ {}", result.name);
            passed += 1;
        } else {
            println!("✗ {}: {}", result.name, result.error.as_ref().unwrap());
        }
    }
    
    println!("\nPassed: {}/{}", passed, results.len());
}
