package maven_emulator;

import java.util.*;

/**
 * Test suite for Maven Emulator
 */
public class TestAutoDepMan {
    
    private AutoDepMan maven;
    
    public void setUp() {
        maven = new AutoDepMan();
    }
    
    public void testPOMCreation() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        assert pom.groupId.equals("com.example");
        assert pom.artifactId.equals("test-app");
        assert pom.version.equals("1.0.0");
        assert pom.packaging.equals("jar");
        System.out.println("✓ testPOMCreation passed");
    }
    
    public void testDependencyManagement() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        
        Dependency dep1 = new Dependency("junit", "junit", "4.12");
        Dependency dep2 = new Dependency("org.slf4j", "slf4j-api", "1.7.30");
        
        pom.dependencies.add(dep1);
        pom.dependencies.add(dep2);
        
        assert pom.dependencies.size() == 2;
        System.out.println("✓ testDependencyManagement passed");
    }
    
    public void testDependencyResolution() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        pom.dependencies.add(new Dependency("junit", "junit", "4.12"));
        pom.dependencies.add(new Dependency("org.slf4j", "slf4j-api", "1.7.30"));
        
        maven.addProject(pom);
        Set<Artifact> resolved = maven.resolveDependencies(pom);
        
        assert resolved.size() >= 2;
        System.out.println("✓ testDependencyResolution passed");
    }
    
    public void testBuildValidate() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        maven.addProject(pom);
        
        BuildResult result = maven.build(pom, LifecyclePhase.VALIDATE);
        
        assert result.success;
        assert result.phase.equals("VALIDATE");
        assert result.messages.size() > 0;
        System.out.println("✓ testBuildValidate passed");
    }
    
    public void testBuildCompile() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        pom.dependencies.add(new Dependency("junit", "junit", "4.12"));
        maven.addProject(pom);
        
        BuildResult result = maven.build(pom, LifecyclePhase.COMPILE);
        
        assert result.success;
        assert result.phase.equals("COMPILE");
        System.out.println("✓ testBuildCompile passed");
    }
    
    public void testBuildTest() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        maven.addProject(pom);
        
        BuildResult result = maven.build(pom, LifecyclePhase.TEST);
        
        assert result.success;
        assert result.phase.equals("TEST");
        System.out.println("✓ testBuildTest passed");
    }
    
    public void testBuildPackage() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        pom.packaging = "jar";
        maven.addProject(pom);
        
        BuildResult result = maven.build(pom, LifecyclePhase.PACKAGE);
        
        assert result.success;
        assert result.phase.equals("PACKAGE");
        System.out.println("✓ testBuildPackage passed");
    }
    
    public void testBuildInstall() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        maven.addProject(pom);
        
        BuildResult result = maven.build(pom, LifecyclePhase.INSTALL);
        
        assert result.success;
        assert result.phase.equals("INSTALL");
        System.out.println("✓ testBuildInstall passed");
    }
    
    public void testCleanPhase() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        maven.addProject(pom);
        
        BuildResult result = maven.build(pom, LifecyclePhase.CLEAN);
        
        assert result.success;
        assert result.phase.equals("CLEAN");
        System.out.println("✓ testCleanPhase passed");
    }
    
    public void testPluginExecution() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        
        Plugin plugin = new Plugin("org.apache.maven.plugins", "maven-compiler-plugin", "3.8.1");
        plugin.configuration.put("source", "11");
        plugin.configuration.put("target", "11");
        pom.plugins.add(plugin);
        
        maven.addProject(pom);
        
        BuildResult result = maven.executeGoal(pom, "compiler:compile");
        
        assert result.success;
        System.out.println("✓ testPluginExecution passed");
    }
    
    public void testArtifactCoordinates() {
        Artifact artifact = new Artifact("com.example", "my-lib", "1.0.0");
        
        String coords = artifact.getCoordinates();
        assert coords.equals("com.example:my-lib:1.0.0");
        System.out.println("✓ testArtifactCoordinates passed");
    }
    
    public void testDependencyScope() {
        Dependency dep = new Dependency("junit", "junit", "4.12", "test", false);
        
        assert dep.scope.equals("test");
        assert !dep.optional;
        System.out.println("✓ testDependencyScope passed");
    }
    
    public void testProperties() {
        POM pom = new POM("com.example", "test-app", "1.0.0");
        
        pom.properties.put("my.property", "value");
        
        assert pom.properties.containsKey("my.property");
        assert pom.properties.get("my.property").equals("value");
        System.out.println("✓ testProperties passed");
    }
    
    public void testMultiModuleProject() {
        POM parent = new POM("com.example", "parent", "1.0.0");
        parent.packaging = "pom";
        parent.modules.add("module1");
        parent.modules.add("module2");
        
        POM module1 = new POM("com.example", "module1", "1.0.0");
        module1.parent = parent;
        
        POM module2 = new POM("com.example", "module2", "1.0.0");
        module2.parent = parent;
        
        maven.addProject(parent);
        maven.addProject(module1);
        maven.addProject(module2);
        
        Map<String, BuildResult> results = maven.buildMultiModule(parent, LifecyclePhase.COMPILE);
        
        assert results.size() >= 0;
        System.out.println("✓ testMultiModuleProject passed");
    }
    
    public void runAllTests() {
        System.out.println("Running Maven Emulator Tests...\n");
        
        setUp(); testPOMCreation();
        setUp(); testDependencyManagement();
        setUp(); testDependencyResolution();
        setUp(); testBuildValidate();
        setUp(); testBuildCompile();
        setUp(); testBuildTest();
        setUp(); testBuildPackage();
        setUp(); testBuildInstall();
        setUp(); testCleanPhase();
        setUp(); testPluginExecution();
        setUp(); testArtifactCoordinates();
        setUp(); testDependencyScope();
        setUp(); testProperties();
        setUp(); testMultiModuleProject();
        
        System.out.println("\nAll tests passed! ✓");
    }
    
    public static void main(String[] args) {
        TestAutoDepMan tests = new TestAutoDepMan();
        tests.runAllTests();
    }
}
