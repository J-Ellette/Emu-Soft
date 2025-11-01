/**
 * Developed by PowerShield, as an alternative to Gradle
 */

package gradle_emulator;

import java.util.*;
import java.io.*;

/**
 * Gradle Emulator - Build Automation Tool
 * 
 * This emulates core Gradle functionality including:
 * - Build script (build.gradle) management
 * - Dependency resolution
 * - Task execution and dependency graphs
 * - Plugin management
 * - Multi-project builds
 * - Build lifecycle (initialization, configuration, execution)
 */

// Gradle dependency
class GradleDependency {
    String group;
    String name;
    String version;
    String configuration; // compile, implementation, testImplementation, etc.
    
    public GradleDependency(String group, String name, String version, String configuration) {
        this.group = group;
        this.name = name;
        this.version = version;
        this.configuration = configuration;
    }
    
    public String getNotation() {
        return group + ":" + name + ":" + version;
    }
    
    @Override
    public String toString() {
        return configuration + " '" + getNotation() + "'";
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof GradleDependency)) return false;
        GradleDependency that = (GradleDependency) o;
        return Objects.equals(group, that.group) &&
               Objects.equals(name, that.name) &&
               Objects.equals(version, that.version);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(group, name, version);
    }
}

// Gradle task
class GradleTask {
    String name;
    String description;
    String group;
    List<String> dependsOn;
    Runnable action;
    boolean executed;
    
    public GradleTask(String name) {
        this.name = name;
        this.description = "";
        this.group = "other";
        this.dependsOn = new ArrayList<>();
        this.executed = false;
    }
    
    public void setAction(Runnable action) {
        this.action = action;
    }
    
    public void execute() {
        if (!executed) {
            System.out.println("> Task :" + name);
            if (action != null) {
                action.run();
            }
            executed = true;
        }
    }
    
    public void reset() {
        executed = false;
    }
}

// Gradle plugin
class GradlePlugin {
    String id;
    String version;
    Map<String, Object> configuration;
    
    public GradlePlugin(String id) {
        this(id, null);
    }
    
    public GradlePlugin(String id, String version) {
        this.id = id;
        this.version = version;
        this.configuration = new HashMap<>();
    }
    
    public void apply(GradleProject project) {
        // Apply plugin to project
        System.out.println("Applying plugin: " + id);
        
        // Add standard tasks based on plugin type
        if (id.equals("java")) {
            project.addTask(new GradleTask("compileJava"));
            project.addTask(new GradleTask("processResources"));
            project.addTask(new GradleTask("classes"));
            project.addTask(new GradleTask("jar"));
            project.addTask(new GradleTask("test"));
            project.addTask(new GradleTask("build"));
        } else if (id.equals("application")) {
            project.addTask(new GradleTask("run"));
        } else if (id.equals("maven-publish")) {
            project.addTask(new GradleTask("publish"));
        }
    }
}

// Gradle repository
class GradleRepository {
    String name;
    String url;
    
    public GradleRepository(String name, String url) {
        this.name = name;
        this.url = url;
    }
    
    @Override
    public String toString() {
        return name + " (" + url + ")";
    }
}

// Gradle project (build.gradle)
class GradleProject {
    String name;
    String group;
    String version;
    String description;
    
    Map<String, GradleTask> tasks;
    List<GradleDependency> dependencies;
    List<GradlePlugin> plugins;
    List<GradleRepository> repositories;
    Map<String, Object> properties;
    
    // Sub-projects for multi-project builds
    List<GradleProject> subprojects;
    GradleProject rootProject;
    
    public GradleProject(String name) {
        this.name = name;
        this.group = "com.example";
        this.version = "1.0.0";
        this.description = "";
        this.tasks = new LinkedHashMap<>();
        this.dependencies = new ArrayList<>();
        this.plugins = new ArrayList<>();
        this.repositories = new ArrayList<>();
        this.properties = new HashMap<>();
        this.subprojects = new ArrayList<>();
    }
    
    public void setGroup(String group) {
        this.group = group;
    }
    
    public void setVersion(String version) {
        this.version = version;
    }
    
    public void addPlugin(GradlePlugin plugin) {
        plugins.add(plugin);
        plugin.apply(this);
    }
    
    public void addRepository(GradleRepository repo) {
        repositories.add(repo);
    }
    
    public void addDependency(GradleDependency dependency) {
        dependencies.add(dependency);
    }
    
    public void addTask(GradleTask task) {
        tasks.put(task.name, task);
    }
    
    public GradleTask task(String name) {
        GradleTask task = new GradleTask(name);
        addTask(task);
        return task;
    }
    
    public GradleTask getTask(String name) {
        return tasks.get(name);
    }
    
    public void addSubproject(GradleProject subproject) {
        subproject.rootProject = this;
        subprojects.add(subproject);
    }
}

// Gradle build
public class GradleBuild {
    GradleProject rootProject;
    Map<String, GradleProject> allProjects;
    
    // Standard repositories
    private static final GradleRepository MAVEN_CENTRAL = 
        new GradleRepository("MavenCentral", "https://repo.maven.apache.org/maven2/");
    private static final GradleRepository MAVEN_LOCAL =
        new GradleRepository("MavenLocal", System.getProperty("user.home") + "/.m2/repository");
    private static final GradleRepository GOOGLE =
        new GradleRepository("Google", "https://maven.google.com/");
    
    public GradleBuild(String projectName) {
        this.rootProject = new GradleProject(projectName);
        this.allProjects = new HashMap<>();
        this.allProjects.put(projectName, rootProject);
    }
    
    public GradleProject getRootProject() {
        return rootProject;
    }
    
    public GradleProject getProject(String name) {
        return allProjects.get(name);
    }
    
    // DSL-style methods
    public void group(String group) {
        rootProject.setGroup(group);
    }
    
    public void version(String version) {
        rootProject.setVersion(version);
    }
    
    public void plugins(PluginSpec spec) {
        spec.apply(rootProject);
    }
    
    public void repositories(RepositorySpec spec) {
        spec.apply(rootProject);
    }
    
    public void dependencies(DependencySpec spec) {
        spec.apply(rootProject);
    }
    
    // Execute tasks
    public void executeTask(String taskName) {
        System.out.println("\n> Configure project :" + rootProject.name);
        
        GradleTask task = rootProject.getTask(taskName);
        if (task == null) {
            System.err.println("Task '" + taskName + "' not found");
            return;
        }
        
        // Execute task dependencies first
        for (String depName : task.dependsOn) {
            GradleTask depTask = rootProject.getTask(depName);
            if (depTask != null) {
                depTask.execute();
            }
        }
        
        // Execute the task
        task.execute();
        
        System.out.println("\nBUILD SUCCESSFUL");
    }
    
    public void executeTasks(String... taskNames) {
        for (String taskName : taskNames) {
            executeTask(taskName);
        }
    }
    
    // Dependency resolution
    public List<GradleDependency> resolveDependencies(String configuration) {
        List<GradleDependency> resolved = new ArrayList<>();
        
        for (GradleDependency dep : rootProject.dependencies) {
            if (dep.configuration.equals(configuration) || 
                configuration.equals("all")) {
                resolved.add(dep);
            }
        }
        
        return resolved;
    }
    
    // Show project info
    public void showProjectInfo() {
        System.out.println("------------------------------------------------------------");
        System.out.println("Root project '" + rootProject.name + "'");
        System.out.println("------------------------------------------------------------");
        System.out.println();
        System.out.println("Group: " + rootProject.group);
        System.out.println("Version: " + rootProject.version);
        System.out.println();
        
        if (!rootProject.plugins.isEmpty()) {
            System.out.println("Plugins:");
            for (GradlePlugin plugin : rootProject.plugins) {
                System.out.println("  - " + plugin.id + 
                    (plugin.version != null ? " (version " + plugin.version + ")" : ""));
            }
            System.out.println();
        }
        
        if (!rootProject.repositories.isEmpty()) {
            System.out.println("Repositories:");
            for (GradleRepository repo : rootProject.repositories) {
                System.out.println("  - " + repo);
            }
            System.out.println();
        }
        
        if (!rootProject.dependencies.isEmpty()) {
            System.out.println("Dependencies:");
            for (GradleDependency dep : rootProject.dependencies) {
                System.out.println("  - " + dep);
            }
            System.out.println();
        }
        
        System.out.println("Tasks:");
        for (GradleTask task : rootProject.tasks.values()) {
            System.out.println("  - " + task.name + 
                (task.description.isEmpty() ? "" : " - " + task.description));
        }
    }
    
    // Plugin specification DSL
    public interface PluginSpec {
        void apply(GradleProject project);
    }
    
    // Repository specification DSL
    public interface RepositorySpec {
        void apply(GradleProject project);
    }
    
    // Dependency specification DSL
    public interface DependencySpec {
        void apply(GradleProject project);
    }
    
    // Helper methods for DSL
    public static PluginSpec java() {
        return project -> project.addPlugin(new GradlePlugin("java"));
    }
    
    public static PluginSpec application() {
        return project -> project.addPlugin(new GradlePlugin("application"));
    }
    
    public static PluginSpec mavenPublish() {
        return project -> project.addPlugin(new GradlePlugin("maven-publish"));
    }
    
    public static RepositorySpec mavenCentral() {
        return project -> project.addRepository(MAVEN_CENTRAL);
    }
    
    public static RepositorySpec mavenLocal() {
        return project -> project.addRepository(MAVEN_LOCAL);
    }
    
    public static RepositorySpec google() {
        return project -> project.addRepository(GOOGLE);
    }
    
    public static DependencySpec implementation(String notation) {
        return project -> {
            String[] parts = notation.split(":");
            project.addDependency(new GradleDependency(
                parts[0], parts[1], parts[2], "implementation"));
        };
    }
    
    public static DependencySpec testImplementation(String notation) {
        return project -> {
            String[] parts = notation.split(":");
            project.addDependency(new GradleDependency(
                parts[0], parts[1], parts[2], "testImplementation"));
        };
    }
    
    // Demo
    public static void main(String[] args) {
        System.out.println("=== Gradle Build Tool Emulator Demo ===\n");
        
        // Create a Gradle build
        GradleBuild build = new GradleBuild("my-application");
        
        // Configure project
        build.group("com.example");
        build.version("1.0.0");
        
        // Apply plugins
        build.plugins(java());
        build.plugins(application());
        
        // Add repositories
        build.repositories(mavenCentral());
        build.repositories(mavenLocal());
        
        // Add dependencies
        build.dependencies(implementation("org.springframework.boot:spring-boot-starter:2.7.0"));
        build.dependencies(implementation("com.google.guava:guava:31.1-jre"));
        build.dependencies(testImplementation("junit:junit:4.13.2"));
        build.dependencies(testImplementation("org.mockito:mockito-core:4.6.1"));
        
        // Add custom tasks
        GradleTask hello = build.getRootProject().task("hello");
        hello.description = "Prints a greeting";
        hello.setAction(() -> {
            System.out.println("Hello from Gradle!");
        });
        
        GradleTask printVersion = build.getRootProject().task("printVersion");
        printVersion.description = "Prints project version";
        printVersion.setAction(() -> {
            System.out.println("Project version: " + build.getRootProject().version);
        });
        
        // Show project information
        System.out.println("1. Project Information");
        System.out.println("=".repeat(60));
        build.showProjectInfo();
        
        // Execute tasks
        System.out.println("\n2. Executing Tasks");
        System.out.println("=".repeat(60));
        
        System.out.println("\n[Running: gradle hello]");
        build.executeTask("hello");
        
        System.out.println("\n[Running: gradle printVersion]");
        build.executeTask("printVersion");
        
        System.out.println("\n[Running: gradle build]");
        build.executeTask("build");
        
        // Resolve dependencies
        System.out.println("\n3. Dependency Resolution");
        System.out.println("=".repeat(60));
        
        System.out.println("\nImplementation dependencies:");
        List<GradleDependency> implDeps = build.resolveDependencies("implementation");
        for (GradleDependency dep : implDeps) {
            System.out.println("  - " + dep.getNotation());
        }
        
        System.out.println("\nTest dependencies:");
        List<GradleDependency> testDeps = build.resolveDependencies("testImplementation");
        for (GradleDependency dep : testDeps) {
            System.out.println("  - " + dep.getNotation());
        }
        
        System.out.println("\n4. Build Complete");
        System.out.println("=".repeat(60));
        System.out.println("✓ Project configured successfully");
        System.out.println("✓ All tasks executed");
        System.out.println("✓ Dependencies resolved");
    }
}
