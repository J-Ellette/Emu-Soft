# Maven Emulator - Build Automation and Dependency Management

A lightweight emulation of **Maven**, the popular build automation and dependency management tool for Java projects.

## Features

This emulator implements core Maven functionality:

### Project Object Model (POM)
- **POM Definition**: Define project coordinates (groupId, artifactId, version)
- **Packaging Types**: Support for jar, war, pom packaging
- **Properties**: Define and use build properties
- **Parent POM**: Inherit configuration from parent projects
- **Multi-Module Projects**: Manage multiple related projects

### Dependency Management
- **Dependency Declaration**: Declare project dependencies with coordinates
- **Dependency Scope**: Support compile, test, runtime, provided scopes
- **Optional Dependencies**: Mark dependencies as optional
- **Dependency Resolution**: Resolve dependency graphs
- **Local Repository**: Simulate Maven local repository (~/.m2/repository)
- **Remote Repositories**: Configure remote Maven repositories

### Build Lifecycle
- **Default Lifecycle**: validate, compile, test, package, install, deploy
- **Clean Lifecycle**: Clean project build artifacts
- **Phase Execution**: Execute specific lifecycle phases
- **Phase Ordering**: Automatic execution of prerequisite phases

### Plugin System
- **Plugin Declaration**: Configure Maven plugins
- **Plugin Execution**: Execute plugin goals
- **Configuration**: Configure plugin parameters
- **Common Plugins**: Compiler, surefire, jar plugins

### Build Operations
- **Compilation**: Compile source code
- **Testing**: Run unit tests
- **Packaging**: Create JAR/WAR artifacts
- **Installation**: Install artifacts to local repository
- **Deployment**: Deploy artifacts to remote repositories

## What It Emulates

This tool emulates core functionality of [Apache Maven](https://maven.apache.org/), the industry-standard build tool for Java projects used by millions of developers.

### Core Components Implemented

1. **Project Object Model (POM)**
   - Project coordinates and metadata
   - Dependency declarations
   - Plugin configuration
   - Build properties

2. **Dependency Resolution**
   - Dependency graph resolution
   - Repository lookup
   - Artifact caching

3. **Build Lifecycle**
   - Default lifecycle phases
   - Clean lifecycle
   - Phase sequencing

4. **Plugin Execution**
   - Plugin goal execution
   - Plugin configuration
   - Built-in plugins

## Usage

### Basic Project Setup

```java
import maven_emulator.*;

// Create Maven emulator
MavenEmulator maven = new MavenEmulator();

// Create project
POM pom = new POM("com.example", "my-app", "1.0.0");
pom.name = "My Application";
pom.description = "A sample Maven project";
pom.packaging = "jar";

// Add to emulator
maven.addProject(pom);
```

### Dependency Management

```java
// Add dependencies
pom.dependencies.add(
    new Dependency("junit", "junit", "4.12", "test", false)
);

pom.dependencies.add(
    new Dependency("org.slf4j", "slf4j-api", "1.7.30")
);

pom.dependencies.add(
    new Dependency("com.google.guava", "guava", "30.0-jre")
);

// Resolve dependencies
Set<Artifact> resolved = maven.resolveDependencies(pom);
System.out.println("Resolved " + resolved.size() + " dependencies");
```

### Build Lifecycle Execution

```java
// Validate project
BuildResult result = maven.build(pom, LifecyclePhase.VALIDATE);
System.out.println("Validation: " + (result.success ? "SUCCESS" : "FAILED"));

// Compile project
result = maven.build(pom, LifecyclePhase.COMPILE);

// Run tests
result = maven.build(pom, LifecyclePhase.TEST);

// Package project
result = maven.build(pom, LifecyclePhase.PACKAGE);

// Install to local repository
result = maven.build(pom, LifecyclePhase.INSTALL);

// Display build messages
for (String message : result.messages) {
    System.out.println(message);
}

System.out.println("Build duration: " + result.duration + "ms");
```

### Plugin Configuration

```java
// Add compiler plugin
Plugin compilerPlugin = new Plugin(
    "org.apache.maven.plugins",
    "maven-compiler-plugin",
    "3.8.1"
);
compilerPlugin.configuration.put("source", "11");
compilerPlugin.configuration.put("target", "11");
pom.plugins.add(compilerPlugin);

// Add surefire plugin for testing
Plugin surefirePlugin = new Plugin(
    "org.apache.maven.plugins",
    "maven-surefire-plugin",
    "2.22.2"
);
pom.plugins.add(surefirePlugin);

// Execute specific plugin goal
BuildResult goalResult = maven.executeGoal(pom, "compiler:compile");
```

### Multi-Module Projects

```java
// Create parent POM
POM parent = new POM("com.example", "parent", "1.0.0");
parent.packaging = "pom";
parent.name = "Parent Project";

// Add modules
parent.modules.add("module-core");
parent.modules.add("module-web");
parent.modules.add("module-api");

// Create module POMs
POM coreModule = new POM("com.example", "module-core", "1.0.0");
coreModule.parent = parent;

POM webModule = new POM("com.example", "module-web", "1.0.0");
webModule.parent = parent;
webModule.dependencies.add(
    new Dependency("com.example", "module-core", "1.0.0")
);

POM apiModule = new POM("com.example", "module-api", "1.0.0");
apiModule.parent = parent;
apiModule.dependencies.add(
    new Dependency("com.example", "module-core", "1.0.0")
);

// Add all to emulator
maven.addProject(parent);
maven.addProject(coreModule);
maven.addProject(webModule);
maven.addProject(apiModule);

// Build all modules
Map<String, BuildResult> results = maven.buildMultiModule(
    parent,
    LifecyclePhase.INSTALL
);

// Check results
for (Map.Entry<String, BuildResult> entry : results.entrySet()) {
    System.out.println("Module: " + entry.getKey());
    System.out.println("Success: " + entry.getValue().success);
}
```

### Properties and Variables

```java
// Set properties
pom.properties.put("project.build.sourceEncoding", "UTF-8");
pom.properties.put("maven.compiler.source", "11");
pom.properties.put("maven.compiler.target", "11");
pom.properties.put("junit.version", "4.12");

// Use property in dependency (in real Maven)
// <dependency>
//   <groupId>junit</groupId>
//   <artifactId>junit</artifactId>
//   <version>${junit.version}</version>
// </dependency>
```

### Complete Example

```java
public class MavenExample {
    public static void main(String[] args) {
        // Initialize Maven
        MavenEmulator maven = new MavenEmulator();
        
        // Create web application project
        POM webApp = new POM("com.example", "webapp", "1.0.0");
        webApp.name = "Web Application";
        webApp.packaging = "war";
        
        // Add dependencies
        webApp.dependencies.add(
            new Dependency("javax.servlet", "javax.servlet-api", "4.0.1", "provided", false)
        );
        webApp.dependencies.add(
            new Dependency("org.springframework", "spring-webmvc", "5.3.0")
        );
        webApp.dependencies.add(
            new Dependency("junit", "junit", "4.12", "test", false)
        );
        
        // Configure plugins
        Plugin compiler = new Plugin(
            "org.apache.maven.plugins",
            "maven-compiler-plugin",
            "3.8.1"
        );
        compiler.configuration.put("source", "11");
        compiler.configuration.put("target", "11");
        webApp.plugins.add(compiler);
        
        Plugin war = new Plugin(
            "org.apache.maven.plugins",
            "maven-war-plugin",
            "3.3.1"
        );
        webApp.plugins.add(war);
        
        // Add project
        maven.addProject(webApp);
        
        // Execute full build
        System.out.println("=== Building Web Application ===\n");
        BuildResult result = maven.build(webApp, LifecyclePhase.PACKAGE);
        
        // Display results
        for (String message : result.messages) {
            System.out.println(message);
        }
        
        if (result.success) {
            System.out.println("\nBuild completed in " + result.duration + "ms");
        }
    }
}
```

## Testing

Compile and run tests:

```bash
javac maven_emulator/*.java
java maven_emulator.TestMavenEmulator
```

## Use Cases

1. **Learning Maven**: Understand Maven concepts without complex setup
2. **Build Tool Development**: Develop tools that interact with Maven
3. **Testing**: Test Maven-dependent code without actual Maven
4. **Education**: Teaching build automation concepts
5. **Prototyping**: Quickly prototype build configurations

## Key Differences from Real Maven

1. **No Actual Compilation**: Doesn't invoke javac
2. **Simplified Resolution**: Basic dependency resolution without full transitive dependencies
3. **No Repository Protocol**: Doesn't download from actual repositories
4. **Limited Plugins**: Only core plugin behaviors emulated
5. **No POM Parsing**: No XML parsing of pom.xml files
6. **In-Memory Only**: No persistent storage

## Real Maven Features Emulated

- Project Object Model (POM) structure
- Dependency management and resolution
- Build lifecycle (validate, compile, test, package, install, deploy)
- Plugin system and execution
- Multi-module projects
- Properties and configuration
- Local repository simulation
- Build result reporting

## License

Educational emulator for learning purposes.

## References

- [Apache Maven Documentation](https://maven.apache.org/guides/)
- [Maven POM Reference](https://maven.apache.org/pom.html)
- [Maven Build Lifecycle](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html)
- [Maven Plugins](https://maven.apache.org/plugins/)
