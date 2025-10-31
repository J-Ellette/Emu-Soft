# Gradle Build Tool Emulator - Build Automation

A lightweight emulation of **Gradle** build automation functionality for Java and other JVM projects.

## Features

This emulator implements core Gradle functionality:

### Build Configuration
- **Project Configuration**: Group, version, and metadata
- **Build Scripts**: Build.gradle-style configuration
- **Plugins**: Java, application, maven-publish plugins
- **Repositories**: Maven Central, Maven Local, Google
- **Dependencies**: Implementation, testImplementation configurations

### Task Management
- **Task Definition**: Create custom tasks
- **Task Dependencies**: Task execution ordering
- **Task Execution**: Run tasks individually or in sequence
- **Built-in Tasks**: Standard Java build tasks

### Dependency Management
- **Dependency Declaration**: Gradle notation (group:name:version)
- **Configurations**: implementation, testImplementation, etc.
- **Dependency Resolution**: Resolve dependencies by configuration
- **Repository Management**: Multiple repository support

### Plugin System
- **Plugin Application**: Apply plugins to projects
- **Java Plugin**: Standard Java build tasks
- **Application Plugin**: Run tasks for applications
- **Maven Publish**: Publishing artifacts

## What It Emulates

This tool emulates core functionality of [Gradle](https://gradle.org/), the popular build automation tool used for Java, Kotlin, Android, and other JVM projects.

### Core Components Implemented

1. **Build Configuration**
   - Project model (group, version)
   - Plugin management
   - Repository configuration
   - Dependency declarations

2. **Task System**
   - Task registration
   - Task execution
   - Task dependencies
   - Custom tasks

3. **Dependency Management**
   - Dependency resolution
   - Configuration management
   - Repository integration

## Usage

### Basic Build Setup

```java
import gradle_emulator.*;

// Create a Gradle build
GradleBuild build = new GradleBuild("my-app");

// Configure project
build.group("com.example");
build.version("1.0.0");

// Apply plugins
build.plugins(GradleBuild.java());
build.plugins(GradleBuild.application());

// Add repositories
build.repositories(GradleBuild.mavenCentral());
build.repositories(GradleBuild.mavenLocal());

// Add dependencies
build.dependencies(
    GradleBuild.implementation("com.google.guava:guava:31.1-jre")
);
build.dependencies(
    GradleBuild.testImplementation("junit:junit:4.13.2")
);
```

### Custom Tasks

```java
// Create a custom task
GradleTask hello = build.getRootProject().task("hello");
hello.description = "Prints a greeting";
hello.setAction(() -> {
    System.out.println("Hello from Gradle!");
});

// Execute the task
build.executeTask("hello");
```

### Task Dependencies

```java
// Create tasks with dependencies
GradleTask compile = build.getRootProject().task("compile");
compile.setAction(() -> {
    System.out.println("Compiling Java sources...");
});

GradleTask test = build.getRootProject().task("test");
test.dependsOn.add("compile");
test.setAction(() -> {
    System.out.println("Running tests...");
});

// Executing 'test' will automatically execute 'compile' first
build.executeTask("test");
```

### Multiple Tasks

```java
// Execute multiple tasks in sequence
build.executeTasks("clean", "compileJava", "test", "jar");
```

### Dependency Resolution

```java
// Resolve dependencies for a configuration
List<GradleDependency> deps = build.resolveDependencies("implementation");

for (GradleDependency dep : deps) {
    System.out.println(dep.getNotation());
}
```

### Project Information

```java
// Display project configuration
build.showProjectInfo();
// Output:
// Root project 'my-app'
// Group: com.example
// Version: 1.0.0
// Plugins: java, application
// Dependencies: ...
// Tasks: ...
```

### Spring Boot Application

```java
// Configure Spring Boot project
GradleBuild build = new GradleBuild("spring-boot-app");
build.group("com.example");
build.version("0.0.1-SNAPSHOT");

// Apply plugins
build.plugins(GradleBuild.java());
build.plugins(GradleBuild.application());

// Repositories
build.repositories(GradleBuild.mavenCentral());

// Spring Boot dependencies
build.dependencies(
    GradleBuild.implementation("org.springframework.boot:spring-boot-starter-web:2.7.0")
);
build.dependencies(
    GradleBuild.implementation("org.springframework.boot:spring-boot-starter-data-jpa:2.7.0")
);
build.dependencies(
    GradleBuild.implementation("com.h2database:h2:2.1.214")
);
build.dependencies(
    GradleBuild.testImplementation("org.springframework.boot:spring-boot-starter-test:2.7.0")
);

// Show configuration
build.showProjectInfo();

// Run build
build.executeTask("build");
```

### Multi-Configuration Dependencies

```java
// Add various dependency types
GradleProject project = build.getRootProject();

// Runtime dependencies
project.addDependency(new GradleDependency(
    "org.slf4j", "slf4j-api", "1.7.36", "implementation"
));

// Test dependencies
project.addDependency(new GradleDependency(
    "org.junit.jupiter", "junit-jupiter", "5.8.2", "testImplementation"
));
project.addDependency(new GradleDependency(
    "org.mockito", "mockito-core", "4.6.1", "testImplementation"
));

// Resolve by configuration
List<GradleDependency> runtimeDeps = build.resolveDependencies("implementation");
List<GradleDependency> testDeps = build.resolveDependencies("testImplementation");
```

## Testing

```bash
# Compile
javac java/gradle_emulator_tool/GradleBuild.java

# Run demo
java -cp java gradle_emulator.GradleBuild
```

The demo will demonstrate:
1. Project configuration
2. Plugin application
3. Repository setup
4. Dependency management
5. Task creation and execution
6. Dependency resolution

## Gradle Concepts

### Plugins
- **java**: Adds Java compilation tasks
- **application**: Adds run task for applications
- **maven-publish**: Adds publishing tasks

### Configurations
- **implementation**: Compile and runtime dependencies
- **testImplementation**: Test-only dependencies
- **compileOnly**: Compile-only dependencies (not runtime)
- **runtimeOnly**: Runtime-only dependencies

### Tasks
- **compileJava**: Compile Java source files
- **processResources**: Copy resources
- **classes**: Assemble compiled classes
- **jar**: Create JAR file
- **test**: Run tests
- **build**: Full build

### Repositories
- **mavenCentral()**: Maven Central repository
- **mavenLocal()**: Local Maven repository (~/.m2)
- **google()**: Google's Maven repository

## Use Cases

1. **Learning**: Understand Gradle build concepts
2. **Testing**: Mock Gradle builds for testing
3. **Prototyping**: Quick build configuration experiments
4. **Education**: Teaching build automation
5. **Development**: Test build logic

## Key Differences from Real Gradle

1. **No Groovy/Kotlin DSL**: Simplified Java API
2. **No Actual Building**: Simulates tasks, doesn't compile
3. **Limited Plugins**: Subset of standard plugins
4. **No Incremental Builds**: No caching or up-to-date checks
5. **Simplified Dependencies**: No transitive resolution
6. **No Daemon**: Direct execution only

## License

Educational emulator for learning purposes.

## References

- [Gradle User Guide](https://docs.gradle.org/current/userguide/userguide.html)
- [Gradle Build Language Reference](https://docs.gradle.org/current/dsl/)
- [Gradle Plugins](https://docs.gradle.org/current/userguide/plugin_reference.html)
- [Dependency Management](https://docs.gradle.org/current/userguide/dependency_management.html)
