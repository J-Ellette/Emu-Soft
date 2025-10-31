package maven_emulator;

import java.util.*;
import java.io.*;

/**
 * Maven Emulator - Build Automation and Dependency Management
 * 
 * This emulates core Maven functionality including:
 * - Project Object Model (POM) management
 * - Dependency resolution
 * - Build lifecycle execution
 * - Plugin management
 * - Repository management
 * - Multi-module projects
 */

// Maven coordinates
class Artifact {
    String groupId;
    String artifactId;
    String version;
    String packaging;
    String scope;
    
    public Artifact(String groupId, String artifactId, String version) {
        this(groupId, artifactId, version, "jar", "compile");
    }
    
    public Artifact(String groupId, String artifactId, String version, 
                   String packaging, String scope) {
        this.groupId = groupId;
        this.artifactId = artifactId;
        this.version = version;
        this.packaging = packaging;
        this.scope = scope;
    }
    
    public String getCoordinates() {
        return groupId + ":" + artifactId + ":" + version;
    }
    
    @Override
    public String toString() {
        return getCoordinates();
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Artifact)) return false;
        Artifact artifact = (Artifact) o;
        return Objects.equals(groupId, artifact.groupId) &&
               Objects.equals(artifactId, artifact.artifactId) &&
               Objects.equals(version, artifact.version);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(groupId, artifactId, version);
    }
}

// Dependency with scope and optional flag
class Dependency extends Artifact {
    boolean optional;
    List<String> exclusions;
    
    public Dependency(String groupId, String artifactId, String version) {
        super(groupId, artifactId, version);
        this.optional = false;
        this.exclusions = new ArrayList<>();
    }
    
    public Dependency(String groupId, String artifactId, String version,
                     String scope, boolean optional) {
        super(groupId, artifactId, version, "jar", scope);
        this.optional = optional;
        this.exclusions = new ArrayList<>();
    }
}

// Maven plugin
class Plugin {
    String groupId;
    String artifactId;
    String version;
    Map<String, String> configuration;
    List<Execution> executions;
    
    public Plugin(String groupId, String artifactId, String version) {
        this.groupId = groupId;
        this.artifactId = artifactId;
        this.version = version;
        this.configuration = new HashMap<>();
        this.executions = new ArrayList<>();
    }
}

// Plugin execution
class Execution {
    String id;
    String phase;
    List<String> goals;
    
    public Execution(String id, String phase, List<String> goals) {
        this.id = id;
        this.phase = phase;
        this.goals = goals;
    }
}

// Maven repository
class Repository {
    String id;
    String url;
    boolean snapshots;
    boolean releases;
    
    public Repository(String id, String url) {
        this.id = id;
        this.url = url;
        this.snapshots = false;
        this.releases = true;
    }
}

// Project Object Model (POM)
class POM {
    String groupId;
    String artifactId;
    String version;
    String packaging;
    String name;
    String description;
    
    POM parent;
    List<Dependency> dependencies;
    List<Plugin> plugins;
    List<Repository> repositories;
    Map<String, String> properties;
    List<String> modules;
    
    public POM(String groupId, String artifactId, String version) {
        this.groupId = groupId;
        this.artifactId = artifactId;
        this.version = version;
        this.packaging = "jar";
        this.dependencies = new ArrayList<>();
        this.plugins = new ArrayList<>();
        this.repositories = new ArrayList<>();
        this.properties = new HashMap<>();
        this.modules = new ArrayList<>();
        
        // Add default properties
        this.properties.put("project.build.sourceEncoding", "UTF-8");
        this.properties.put("maven.compiler.source", "11");
        this.properties.put("maven.compiler.target", "11");
    }
    
    public String getCoordinates() {
        return groupId + ":" + artifactId + ":" + version;
    }
}

// Build result
class BuildResult {
    boolean success;
    String phase;
    long duration;
    List<String> messages;
    
    public BuildResult(boolean success, String phase) {
        this.success = success;
        this.phase = phase;
        this.duration = 0;
        this.messages = new ArrayList<>();
    }
}

// Maven lifecycle phases
enum LifecyclePhase {
    VALIDATE,
    INITIALIZE,
    GENERATE_SOURCES,
    PROCESS_SOURCES,
    GENERATE_RESOURCES,
    PROCESS_RESOURCES,
    COMPILE,
    PROCESS_CLASSES,
    GENERATE_TEST_SOURCES,
    PROCESS_TEST_SOURCES,
    GENERATE_TEST_RESOURCES,
    PROCESS_TEST_RESOURCES,
    TEST_COMPILE,
    PROCESS_TEST_CLASSES,
    TEST,
    PREPARE_PACKAGE,
    PACKAGE,
    PRE_INTEGRATION_TEST,
    INTEGRATION_TEST,
    POST_INTEGRATION_TEST,
    VERIFY,
    INSTALL,
    DEPLOY,
    CLEAN,
    SITE
}

// Main Maven emulator
public class AutoDepMan {
    private Map<String, POM> projects;
    private Map<String, Artifact> localRepository;
    private List<Repository> remoteRepositories;
    
    public MavenEmulator() {
        this.projects = new HashMap<>();
        this.localRepository = new HashMap<>();
        this.remoteRepositories = new ArrayList<>();
        
        // Add Maven Central
        this.remoteRepositories.add(
            new Repository("central", "https://repo.maven.apache.org/maven2")
        );
    }
    
    // Add project to emulator
    public void addProject(POM pom) {
        projects.put(pom.getCoordinates(), pom);
    }
    
    // Resolve dependencies for a project
    public Set<Artifact> resolveDependencies(POM pom) {
        Set<Artifact> resolved = new HashSet<>();
        Queue<Dependency> toResolve = new LinkedList<>(pom.dependencies);
        Set<String> seen = new HashSet<>();
        
        while (!toResolve.isEmpty()) {
            Dependency dep = toResolve.poll();
            String coords = dep.getCoordinates();
            
            if (seen.contains(coords) || dep.optional) {
                continue;
            }
            seen.add(coords);
            
            // Check if already in local repo
            if (localRepository.containsKey(coords)) {
                resolved.add(localRepository.get(coords));
            } else {
                // Simulate downloading from remote repository
                Artifact artifact = new Artifact(
                    dep.groupId, dep.artifactId, dep.version, 
                    dep.packaging, dep.scope
                );
                localRepository.put(coords, artifact);
                resolved.add(artifact);
            }
            
            // Resolve transitive dependencies (simplified)
            // In real Maven, would parse POM of dependency
        }
        
        return resolved;
    }
    
    // Execute build lifecycle
    public BuildResult build(POM pom, LifecyclePhase targetPhase) {
        long startTime = System.currentTimeMillis();
        BuildResult result = new BuildResult(true, targetPhase.name());
        
        result.messages.add("[INFO] Scanning for projects...");
        result.messages.add("[INFO] Building " + pom.name + " " + pom.version);
        result.messages.add("[INFO] --------------------------------[ " + pom.packaging + " ]---------------------------------");
        
        // Execute phases up to target phase
        List<LifecyclePhase> phases = getPhaseSequence(targetPhase);
        
        for (LifecyclePhase phase : phases) {
            result.messages.add("[INFO] --- Executing phase: " + phase.name().toLowerCase().replace('_', '-') + " ---");
            
            switch (phase) {
                case VALIDATE:
                    executeValidate(pom, result);
                    break;
                case COMPILE:
                    executeCompile(pom, result);
                    break;
                case TEST:
                    executeTest(pom, result);
                    break;
                case PACKAGE:
                    executePackage(pom, result);
                    break;
                case INSTALL:
                    executeInstall(pom, result);
                    break;
                case DEPLOY:
                    executeDeploy(pom, result);
                    break;
                case CLEAN:
                    executeClean(pom, result);
                    break;
                default:
                    result.messages.add("[INFO] Phase " + phase + " completed");
            }
            
            if (!result.success) {
                break;
            }
        }
        
        result.duration = System.currentTimeMillis() - startTime;
        
        if (result.success) {
            result.messages.add("[INFO] ------------------------------------------------------------------------");
            result.messages.add("[INFO] BUILD SUCCESS");
            result.messages.add("[INFO] ------------------------------------------------------------------------");
            result.messages.add("[INFO] Total time: " + result.duration + " ms");
        } else {
            result.messages.add("[ERROR] BUILD FAILURE");
        }
        
        return result;
    }
    
    private List<LifecyclePhase> getPhaseSequence(LifecyclePhase targetPhase) {
        List<LifecyclePhase> phases = new ArrayList<>();
        
        // Build phase sequence based on target
        if (targetPhase == LifecyclePhase.CLEAN) {
            phases.add(LifecyclePhase.CLEAN);
        } else {
            phases.add(LifecyclePhase.VALIDATE);
            
            if (targetPhase.ordinal() >= LifecyclePhase.COMPILE.ordinal()) {
                phases.add(LifecyclePhase.PROCESS_RESOURCES);
                phases.add(LifecyclePhase.COMPILE);
            }
            
            if (targetPhase.ordinal() >= LifecyclePhase.TEST.ordinal()) {
                phases.add(LifecyclePhase.PROCESS_TEST_RESOURCES);
                phases.add(LifecyclePhase.TEST_COMPILE);
                phases.add(LifecyclePhase.TEST);
            }
            
            if (targetPhase.ordinal() >= LifecyclePhase.PACKAGE.ordinal()) {
                phases.add(LifecyclePhase.PACKAGE);
            }
            
            if (targetPhase.ordinal() >= LifecyclePhase.INSTALL.ordinal()) {
                phases.add(LifecyclePhase.INSTALL);
            }
            
            if (targetPhase.ordinal() >= LifecyclePhase.DEPLOY.ordinal()) {
                phases.add(LifecyclePhase.DEPLOY);
            }
        }
        
        return phases;
    }
    
    private void executeValidate(POM pom, BuildResult result) {
        result.messages.add("[INFO] Validating project structure...");
        
        if (pom.groupId == null || pom.artifactId == null || pom.version == null) {
            result.success = false;
            result.messages.add("[ERROR] Invalid POM: missing required fields");
        }
    }
    
    private void executeCompile(POM pom, BuildResult result) {
        result.messages.add("[INFO] Compiling source files...");
        result.messages.add("[INFO] Compiling " + 10 + " source files to target/classes");
        
        // Resolve dependencies
        Set<Artifact> deps = resolveDependencies(pom);
        result.messages.add("[INFO] Using " + deps.size() + " dependencies");
    }
    
    private void executeTest(POM pom, BuildResult result) {
        result.messages.add("[INFO] Running unit tests...");
        result.messages.add("[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0");
    }
    
    private void executePackage(POM pom, BuildResult result) {
        String artifactName = pom.artifactId + "-" + pom.version + "." + pom.packaging;
        result.messages.add("[INFO] Building " + pom.packaging.toUpperCase() + ": target/" + artifactName);
    }
    
    private void executeInstall(POM pom, BuildResult result) {
        String coords = pom.getCoordinates();
        Artifact artifact = new Artifact(pom.groupId, pom.artifactId, pom.version, pom.packaging, "compile");
        localRepository.put(coords, artifact);
        
        result.messages.add("[INFO] Installing artifact to local repository");
        result.messages.add("[INFO] Installed to: ~/.m2/repository/" + 
                          pom.groupId.replace('.', '/') + "/" + 
                          pom.artifactId + "/" + pom.version);
    }
    
    private void executeDeploy(POM pom, BuildResult result) {
        result.messages.add("[INFO] Deploying artifact to remote repository");
    }
    
    private void executeClean(POM pom, BuildResult result) {
        result.messages.add("[INFO] Cleaning project...");
        result.messages.add("[INFO] Deleting target directory");
    }
    
    // Execute specific goal
    public BuildResult executeGoal(POM pom, String pluginGoal) {
        BuildResult result = new BuildResult(true, "goal");
        result.messages.add("[INFO] Executing goal: " + pluginGoal);
        
        // Parse plugin goal (e.g., "compiler:compile")
        String[] parts = pluginGoal.split(":");
        if (parts.length == 2) {
            String pluginName = parts[0];
            String goal = parts[1];
            
            result.messages.add("[INFO] Plugin: " + pluginName + ", Goal: " + goal);
            
            // Execute common plugin goals
            switch (pluginName) {
                case "compiler":
                    if (goal.equals("compile")) {
                        executeCompile(pom, result);
                    }
                    break;
                case "surefire":
                    if (goal.equals("test")) {
                        executeTest(pom, result);
                    }
                    break;
                case "jar":
                    if (goal.equals("jar")) {
                        executePackage(pom, result);
                    }
                    break;
            }
        }
        
        return result;
    }
    
    // Build multi-module project
    public Map<String, BuildResult> buildMultiModule(POM parentPom, LifecyclePhase phase) {
        Map<String, BuildResult> results = new HashMap<>();
        
        System.out.println("[INFO] Reactor Build Order:");
        for (String module : parentPom.modules) {
            System.out.println("[INFO]   " + module);
        }
        
        for (String module : parentPom.modules) {
            // Find module POM
            String moduleCoords = parentPom.groupId + ":" + module + ":" + parentPom.version;
            POM modulePom = projects.get(moduleCoords);
            
            if (modulePom == null) {
                // Create placeholder
                modulePom = new POM(parentPom.groupId, module, parentPom.version);
                modulePom.parent = parentPom;
            }
            
            BuildResult result = build(modulePom, phase);
            results.put(module, result);
            
            if (!result.success) {
                System.out.println("[ERROR] Failed to build module: " + module);
                break;
            }
        }
        
        return results;
    }
    
    // Example usage
    public static void main(String[] args) {
        MavenEmulator maven = new MavenEmulator();
        
        // Create a project
        POM pom = new POM("com.example", "my-app", "1.0.0");
        pom.name = "My Application";
        pom.description = "A sample Maven project";
        pom.packaging = "jar";
        
        // Add dependencies
        pom.dependencies.add(new Dependency("junit", "junit", "4.12", "test", false));
        pom.dependencies.add(new Dependency("org.slf4j", "slf4j-api", "1.7.30"));
        
        // Add plugin
        Plugin compilerPlugin = new Plugin("org.apache.maven.plugins", "maven-compiler-plugin", "3.8.1");
        compilerPlugin.configuration.put("source", "11");
        compilerPlugin.configuration.put("target", "11");
        pom.plugins.add(compilerPlugin);
        
        maven.addProject(pom);
        
        // Build project
        System.out.println("=== Maven Build ===\n");
        BuildResult result = maven.build(pom, LifecyclePhase.INSTALL);
        
        for (String message : result.messages) {
            System.out.println(message);
        }
        
        // Execute specific goal
        System.out.println("\n=== Execute Goal ===\n");
        BuildResult goalResult = maven.executeGoal(pom, "compiler:compile");
        for (String message : goalResult.messages) {
            System.out.println(message);
        }
    }
}
