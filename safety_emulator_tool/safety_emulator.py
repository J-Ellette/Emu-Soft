"""
Safety Emulator - Python Dependency Vulnerability Scanner
Emulates Safety functionality for checking Python dependencies for known security vulnerabilities
"""

import re
import json
import os
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import hashlib


class VulnerabilitySeverity(Enum):
    """Severity levels for vulnerabilities"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class Vulnerability:
    """Represents a known vulnerability in a package"""
    package_name: str
    vulnerable_spec: str
    cve_id: Optional[str]
    advisory: str
    severity: VulnerabilitySeverity
    fixed_in: Optional[str] = None
    
    def __str__(self):
        cve_str = f" ({self.cve_id})" if self.cve_id else ""
        fixed_str = f" Fixed in: {self.fixed_in}" if self.fixed_in else ""
        return (f"{self.package_name} {self.vulnerable_spec}{cve_str} - "
                f"{self.severity.value}: {self.advisory}{fixed_str}")


@dataclass
class InsecurePackage:
    """Represents an installed package with vulnerabilities"""
    package_name: str
    installed_version: str
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    
    def add_vulnerability(self, vuln: Vulnerability):
        """Add a vulnerability to this package"""
        self.vulnerabilities.append(vuln)
    
    def __str__(self):
        vuln_count = len(self.vulnerabilities)
        return (f"{self.package_name} {self.installed_version} "
                f"({vuln_count} {'vulnerability' if vuln_count == 1 else 'vulnerabilities'})")


@dataclass
class ScanResult:
    """Result of a safety scan"""
    scanned_packages: int = 0
    vulnerable_packages: List[InsecurePackage] = field(default_factory=list)
    
    def add_vulnerable_package(self, pkg: InsecurePackage):
        """Add a vulnerable package to results"""
        self.vulnerable_packages.append(pkg)
    
    @property
    def total_vulnerabilities(self) -> int:
        """Get total number of vulnerabilities found"""
        return sum(len(pkg.vulnerabilities) for pkg in self.vulnerable_packages)
    
    @property
    def is_safe(self) -> bool:
        """Check if scan found no vulnerabilities"""
        return len(self.vulnerable_packages) == 0


class VulnerabilityDatabase:
    """
    In-memory vulnerability database.
    In real Safety, this would be fetched from PyUp.io's safety-db.
    This is a simplified version with common known vulnerabilities.
    """
    
    def __init__(self):
        """Initialize vulnerability database"""
        self.vulnerabilities: Dict[str, List[Vulnerability]] = {}
        self._load_default_database()
    
    def _load_default_database(self):
        """Load default vulnerability data"""
        # This is a curated set of known vulnerabilities for demonstration
        # Real Safety uses PyUp.io's safety-db (https://github.com/pyupio/safety-db)
        
        default_vulns = [
            # Django vulnerabilities
            Vulnerability(
                package_name="django",
                vulnerable_spec="<2.2.28",
                cve_id="CVE-2022-28346",
                advisory="SQL injection in QuerySet.annotate(), aggregate(), and extra()",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="2.2.28"
            ),
            Vulnerability(
                package_name="django",
                vulnerable_spec="<3.2.13",
                cve_id="CVE-2022-28347",
                advisory="SQL injection via QuerySet.explain() on PostgreSQL",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="3.2.13"
            ),
            
            # Flask vulnerabilities
            Vulnerability(
                package_name="flask",
                vulnerable_spec="<2.2.5",
                cve_id="CVE-2023-30861",
                advisory="Cookie parsing vulnerability allowing session fixation",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="2.2.5"
            ),
            
            # Requests vulnerabilities
            Vulnerability(
                package_name="requests",
                vulnerable_spec="<2.31.0",
                cve_id="CVE-2023-32681",
                advisory="Unintended leak of Proxy-Authorization header",
                severity=VulnerabilitySeverity.MEDIUM,
                fixed_in="2.31.0"
            ),
            
            # Urllib3 vulnerabilities
            Vulnerability(
                package_name="urllib3",
                vulnerable_spec="<1.26.5",
                cve_id="CVE-2021-33503",
                advisory="HTTP request smuggling due to header injection",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="1.26.5"
            ),
            Vulnerability(
                package_name="urllib3",
                vulnerable_spec="<1.26.17",
                cve_id="CVE-2023-43804",
                advisory="Cookie request header is not stripped on cross-origin redirects",
                severity=VulnerabilitySeverity.MEDIUM,
                fixed_in="1.26.17"
            ),
            
            # PyYAML vulnerabilities
            Vulnerability(
                package_name="pyyaml",
                vulnerable_spec="<5.4",
                cve_id="CVE-2020-14343",
                advisory="Arbitrary code execution via python/object/new constructor",
                severity=VulnerabilitySeverity.CRITICAL,
                fixed_in="5.4"
            ),
            
            # Cryptography vulnerabilities
            Vulnerability(
                package_name="cryptography",
                vulnerable_spec="<41.0.2",
                cve_id="CVE-2023-38325",
                advisory="NULL-pointer dereference in PKCS12 parsing",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="41.0.2"
            ),
            
            # Pillow vulnerabilities
            Vulnerability(
                package_name="pillow",
                vulnerable_spec="<9.0.0",
                cve_id="CVE-2022-22815",
                advisory="Path traversal in ImageFont.truetype",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="9.0.0"
            ),
            
            # Jinja2 vulnerabilities
            Vulnerability(
                package_name="jinja2",
                vulnerable_spec="<2.11.3",
                cve_id="CVE-2020-28493",
                advisory="ReDoS vulnerability in urlize filter",
                severity=VulnerabilitySeverity.MEDIUM,
                fixed_in="2.11.3"
            ),
            
            # SQLAlchemy vulnerabilities
            Vulnerability(
                package_name="sqlalchemy",
                vulnerable_spec="<1.4.45",
                cve_id="CVE-2022-42969",
                advisory="SQL injection in order_by or group_by",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="1.4.45"
            ),
            
            # PyJWT vulnerabilities
            Vulnerability(
                package_name="pyjwt",
                vulnerable_spec="<2.4.0",
                cve_id="CVE-2022-29217",
                advisory="Key confusion through non-blocklisted public key formats",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="2.4.0"
            ),
            
            # Werkzeug vulnerabilities
            Vulnerability(
                package_name="werkzeug",
                vulnerable_spec="<2.2.3",
                cve_id="CVE-2023-25577",
                advisory="High resource usage when parsing multipart form data",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="2.2.3"
            ),
            
            # Certifi vulnerabilities
            Vulnerability(
                package_name="certifi",
                vulnerable_spec="<2022.12.7",
                cve_id="CVE-2022-23491",
                advisory="TrustCor root certificates removed from trust store",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="2022.12.7"
            ),
            
            # NumPy vulnerabilities
            Vulnerability(
                package_name="numpy",
                vulnerable_spec="<1.22.0",
                cve_id="CVE-2021-41496",
                advisory="Buffer overflow in array parsing",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="1.22.0"
            ),
            
            # Setuptools vulnerabilities
            Vulnerability(
                package_name="setuptools",
                vulnerable_spec="<65.5.1",
                cve_id="CVE-2022-40897",
                advisory="Regular expression denial of service in package_index",
                severity=VulnerabilitySeverity.MEDIUM,
                fixed_in="65.5.1"
            ),
            
            # Tornado vulnerabilities
            Vulnerability(
                package_name="tornado",
                vulnerable_spec="<6.1",
                cve_id="CVE-2020-28033",
                advisory="HTTP request smuggling in HTTP/1.1 chunked encoding",
                severity=VulnerabilitySeverity.HIGH,
                fixed_in="6.1"
            ),
        ]
        
        # Organize vulnerabilities by package name
        for vuln in default_vulns:
            pkg_name = vuln.package_name.lower()
            if pkg_name not in self.vulnerabilities:
                self.vulnerabilities[pkg_name] = []
            self.vulnerabilities[pkg_name].append(vuln)
    
    def get_vulnerabilities(self, package_name: str) -> List[Vulnerability]:
        """Get vulnerabilities for a package"""
        return self.vulnerabilities.get(package_name.lower(), [])
    
    def add_vulnerability(self, vuln: Vulnerability):
        """Add a vulnerability to the database"""
        pkg_name = vuln.package_name.lower()
        if pkg_name not in self.vulnerabilities:
            self.vulnerabilities[pkg_name] = []
        self.vulnerabilities[pkg_name].append(vuln)
    
    def load_from_file(self, file_path: str):
        """Load vulnerabilities from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for pkg_name, vulns in data.items():
                for vuln_data in vulns:
                    vuln = Vulnerability(
                        package_name=pkg_name,
                        vulnerable_spec=vuln_data.get('vulnerable_spec', ''),
                        cve_id=vuln_data.get('cve_id'),
                        advisory=vuln_data.get('advisory', ''),
                        severity=VulnerabilitySeverity[vuln_data.get('severity', 'UNKNOWN')],
                        fixed_in=vuln_data.get('fixed_in')
                    )
                    self.add_vulnerability(vuln)
        except Exception as e:
            print(f"Error loading vulnerability database: {e}")
    
    def save_to_file(self, file_path: str):
        """Save vulnerabilities to a JSON file"""
        data = {}
        for pkg_name, vulns in self.vulnerabilities.items():
            data[pkg_name] = [
                {
                    'vulnerable_spec': v.vulnerable_spec,
                    'cve_id': v.cve_id,
                    'advisory': v.advisory,
                    'severity': v.severity.value,
                    'fixed_in': v.fixed_in
                }
                for v in vulns
            ]
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)


class SafetyEmulator:
    """
    Main Safety scanner emulator.
    Scans Python dependencies for known security vulnerabilities.
    """
    
    def __init__(self, db: Optional[VulnerabilityDatabase] = None, verbose: bool = False):
        """
        Initialize Safety emulator.
        
        Args:
            db: Vulnerability database (creates default if None)
            verbose: Enable verbose output
        """
        self.db = db if db else VulnerabilityDatabase()
        self.verbose = verbose
    
    def check_requirements(self, requirements_file: str) -> ScanResult:
        """
        Check requirements file for vulnerabilities.
        
        Args:
            requirements_file: Path to requirements.txt file
            
        Returns:
            ScanResult with vulnerabilities found
        """
        result = ScanResult()
        
        if not os.path.exists(requirements_file):
            if self.verbose:
                print(f"Requirements file not found: {requirements_file}")
            return result
        
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.readlines()
            
            for line in requirements:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse package and version
                pkg_info = self._parse_requirement(line)
                if not pkg_info:
                    continue
                
                pkg_name, version = pkg_info
                result.scanned_packages += 1
                
                # Check for vulnerabilities
                vulns = self._check_package_version(pkg_name, version)
                
                if vulns:
                    insecure_pkg = InsecurePackage(
                        package_name=pkg_name,
                        installed_version=version
                    )
                    for vuln in vulns:
                        insecure_pkg.add_vulnerability(vuln)
                    result.add_vulnerable_package(insecure_pkg)
                    
                    if self.verbose:
                        print(f"Found {len(vulns)} vulnerabilities in {pkg_name} {version}")
        
        except Exception as e:
            if self.verbose:
                print(f"Error checking requirements: {e}")
        
        return result
    
    def check_packages(self, packages: List[Tuple[str, str]]) -> ScanResult:
        """
        Check list of packages for vulnerabilities.
        
        Args:
            packages: List of (package_name, version) tuples
            
        Returns:
            ScanResult with vulnerabilities found
        """
        result = ScanResult()
        
        for pkg_name, version in packages:
            result.scanned_packages += 1
            
            vulns = self._check_package_version(pkg_name, version)
            
            if vulns:
                insecure_pkg = InsecurePackage(
                    package_name=pkg_name,
                    installed_version=version
                )
                for vuln in vulns:
                    insecure_pkg.add_vulnerability(vuln)
                result.add_vulnerable_package(insecure_pkg)
                
                if self.verbose:
                    print(f"Found {len(vulns)} vulnerabilities in {pkg_name} {version}")
        
        return result
    
    def _parse_requirement(self, requirement: str) -> Optional[Tuple[str, str]]:
        """Parse a requirement string into package name and version"""
        # Remove inline comments
        requirement = requirement.split('#')[0].strip()
        
        # Handle various requirement formats
        # package==1.0.0
        # package>=1.0.0
        # package~=1.0.0
        # package
        
        operators = ['===', '==', '>=', '<=', '!=', '~=', '>', '<']
        
        for op in operators:
            if op in requirement:
                parts = requirement.split(op)
                if len(parts) >= 2:
                    pkg_name = parts[0].strip()
                    version = parts[1].strip()
                    # Remove any extras like [dev]
                    pkg_name = pkg_name.split('[')[0].strip()
                    # Remove any trailing operators or conditions
                    version = version.split(',')[0].split(';')[0].strip()
                    return (pkg_name, version)
        
        # No version specified
        pkg_name = requirement.split('[')[0].strip()
        if pkg_name:
            return (pkg_name, 'unknown')
        
        return None
    
    def _check_package_version(self, package_name: str, version: str) -> List[Vulnerability]:
        """Check if a package version is vulnerable"""
        vulns = self.db.get_vulnerabilities(package_name)
        
        if not vulns:
            return []
        
        matching_vulns = []
        
        for vuln in vulns:
            if self._is_version_vulnerable(version, vuln.vulnerable_spec):
                matching_vulns.append(vuln)
        
        return matching_vulns
    
    def _is_version_vulnerable(self, installed_version: str, vulnerable_spec: str) -> bool:
        """
        Check if installed version matches vulnerable specification.
        Simplified version comparison.
        """
        if installed_version == 'unknown':
            return True  # Assume vulnerable if version unknown
        
        # Parse vulnerable spec (e.g., "<2.0.0", ">=1.0.0,<2.0.0")
        if vulnerable_spec.startswith('<'):
            max_version = vulnerable_spec[1:].strip()
            return self._compare_versions(installed_version, max_version) < 0
        elif vulnerable_spec.startswith('<='):
            max_version = vulnerable_spec[2:].strip()
            return self._compare_versions(installed_version, max_version) <= 0
        elif vulnerable_spec.startswith('>='):
            min_version = vulnerable_spec[2:].strip()
            return self._compare_versions(installed_version, min_version) >= 0
        elif vulnerable_spec.startswith('>'):
            min_version = vulnerable_spec[1:].strip()
            return self._compare_versions(installed_version, min_version) > 0
        elif vulnerable_spec.startswith('=='):
            exact_version = vulnerable_spec[2:].strip()
            return installed_version == exact_version
        
        return False
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        Returns: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        Simplified version comparison.
        """
        try:
            # Split versions into parts
            parts1 = [int(x) for x in version1.split('.')]
            parts2 = [int(x) for x in version2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(parts1), len(parts2))
            parts1 += [0] * (max_len - len(parts1))
            parts2 += [0] * (max_len - len(parts2))
            
            # Compare parts
            for p1, p2 in zip(parts1, parts2):
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            
            return 0
        except:
            # If parsing fails, do string comparison
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            return 0
    
    def generate_report(self, result: ScanResult) -> Dict[str, Any]:
        """
        Generate summary report from scan result.
        
        Args:
            result: ScanResult object
            
        Returns:
            Dictionary with summary statistics
        """
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'UNKNOWN': 0
        }
        
        affected_packages = []
        all_cves = []
        
        for pkg in result.vulnerable_packages:
            affected_packages.append(pkg.package_name)
            for vuln in pkg.vulnerabilities:
                severity_counts[vuln.severity.value] += 1
                if vuln.cve_id:
                    all_cves.append(vuln.cve_id)
        
        return {
            'scanned_packages': result.scanned_packages,
            'vulnerable_packages': len(result.vulnerable_packages),
            'total_vulnerabilities': result.total_vulnerabilities,
            'is_safe': result.is_safe,
            'severity_breakdown': severity_counts,
            'affected_packages': affected_packages,
            'cves_found': all_cves
        }


def main():
    """Command-line interface for Safety emulator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python safety_emulator.py <requirements.txt> [-v]")
        print("   or: python safety_emulator.py check <requirements.txt>")
        sys.exit(1)
    
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    # Determine command
    if sys.argv[1] == 'check':
        if len(sys.argv) < 3:
            print("Error: requirements file not specified")
            sys.exit(1)
        requirements_file = sys.argv[2]
    else:
        requirements_file = sys.argv[1]
    
    emulator = SafetyEmulator(verbose=verbose)
    result = emulator.check_requirements(requirements_file)
    
    # Print results
    if result.vulnerable_packages:
        print("\n" + "=" * 80)
        print("VULNERABILITIES FOUND")
        print("=" * 80)
        
        for pkg in result.vulnerable_packages:
            print(f"\n{pkg}")
            for vuln in pkg.vulnerabilities:
                print(f"  -> {vuln}")
    else:
        print("\n" + "=" * 80)
        print("✓ All dependencies are safe!")
        print("=" * 80)
    
    # Print summary
    report = emulator.generate_report(result)
    print("\n" + "=" * 80)
    print("SCAN SUMMARY")
    print("=" * 80)
    print(f"Packages scanned: {report['scanned_packages']}")
    print(f"Vulnerable packages: {report['vulnerable_packages']}")
    print(f"Total vulnerabilities: {report['total_vulnerabilities']}")
    print(f"\nSeverity breakdown:")
    for severity, count in report['severity_breakdown'].items():
        if count > 0:
            print(f"  {severity}: {count}")
    
    # Exit with error code if vulnerabilities found
    sys.exit(0 if result.is_safe else 1)


if __name__ == '__main__':
    main()
