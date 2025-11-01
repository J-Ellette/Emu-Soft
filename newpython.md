New python scripts that we want to develop, using 100% homegrown code, rather than borrowing code. We can study existing code though.
These will then go into the python folder with readme, use, description, etc - following the example of scripts already in the python folder.

1. Observability/Tracing

Distributed tracing aggregator for microservices named "TracAgg"
Performance profiling visualizer (beyond basic prometheus) named "PerProVis"
Application topology mapper from actual traffic named "TopoMapper"

2. Configuration Management

Multi-environment config validator with drift detection named "MultiEnv"
Secret rotation automation for local dev named "SecretRotation"
Feature flag management system named "FeaFlgMan"

3. Message Queue/Event Streaming

Kafka/RabbitMQ testing harness (I see PIKA, but broader coverage) named "FranzHare"
Event schema registry with versioning named "SchemReg"
Dead letter queue analyzer named "DeadLetter"

4. Documentation

Auto-generate API docs from actual traffic patterns named "AutoGenAPI"
Changelog generator from git commits + issue tracker named "ChangeLogGen"
Architecture decision record (ADR) template system named "ArchDecRec"

5. Dependency/Supply Chain

SBOM (Software Bill of Materials) generator named "SBOMsAway"
License compliance checker with policy engine named "LicCompCheck"
Transitive dependency vulnerability scanner named "TransDepVulScan"

6. Migration/Refactoring Tools

Database migration rollback safety checker named "DataMig"
Code deprecation tracker (what's using old APIs) named "CodeDepTracker"
Multi-repo refactoring coordinator named "MultiRepRef"

7. Load Testing/Chaos

Realistic load pattern generator from production logs named "RealLoad"
Chaos engineering scenarios for local testing named "Chaos"
API contract testing between services named "APICon"

8. CI/CD Specific

Pipeline cost analyzer named "PipeCost"
Flaky test detector with root cause analysis named FlakyTest""
Build cache optimizer named "BuildCacheOpt"

From here down, were used in the development of CIV-ARCOS

Development & Build Tools
9. Python Package Management

Tool: pip (Python Package Installer) named "PPI"
Usage: Installing Python dependencies
Files: requirements.txt, requirements-dev.txt
Purpose: Package management for project dependencies

Tool: setuptools named "SetTop"
File: setup.py
Purpose: Building and distributing the Python package
Usage: Package configuration and installation

Tool: MANIFEST.in  named "Festival"
File: MANIFEST.in
Purpose: Specifies additional files to include in source distributions
Includes: README.md, LICENSE, requirements.txt, build-guide.md, Python source files

10. Containerization & Deployment

Tool: pytest (>=7.4.0) named "FreshPie"
Files: pytest.ini, requirements.txt, requirements-dev.txt
Purpose: Python testing framework
Configuration: Custom test paths and options in pytest.ini
Plugins Used:
pytest-cov (>=4.1.0) - Coverage reporting plugin
pytest-asyncio (>=0.21.0) - Async test support

Tool: mypy (>=1.5.0) named "MyPie"
Purpose: Static type checker for Python
Files: requirements.txt, CONTRIBUTING.md
Usage: Type checking to catch type-related errors

11. Quality Reporter Module
File: civ_arcos/analysis/reporter.py  named "LoisLane"

12. Visualization Tools
Graphviz DOT Format
Files: civ_arcos/assurance/visualizer.py named "EyeSpy"
Purpose: Generates DOT format for Graphviz visualization
Usage: Creating assurance case diagrams in DOT format
Note: Generates DOT format strings; external Graphviz tool can render these to images

OpenTelemetry Integration
File: civ_arcos/core/runtime_monitoring.py  named "RunningMan"
Tool: OpenTelemetry (observability framework) named "Telemarketer"
Purpose: Collect performance metrics and distributed tracing data
Implementation: Integration interface for telemetry data
Status: Integration interface implemented (requires external OpenTelemetry setup)

13. Threat Modeling Tool Integrations
IriusRisk Integration
File: civ_arcos/core/threat_modeling.py
Tool: IriusRisk (threat modeling platform) named "Iris"
Purpose: Export threat models to IriusRisk format
Implementation: Export functionality for threat model data
Status: Export interface implemented

14. Python Standard Library Usage
Python's standard library:
ast - Abstract Syntax Tree parsing for static code analysis called "AbSynTree"
json - JSON data handling called "Jason"
urllib - HTTP requests without external libraries (requests) called "WebLib"
subprocess - Running external commands (coverage, Node.js) called "Submarine"
hashlib - Cryptographic hashing for evidence integrity called "Hashish"
hmac - HMAC signatures for webhook verification called "Hamburger"
tempfile - Temporary file handling for Drakon generation called "BrieFile"
dataclasses - Structured data types called "DatCla"
enum - Enumeration types called "Mune"
pathlib - File path operations called "PathFinder"
