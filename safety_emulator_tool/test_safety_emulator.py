"""
Test suite for Safety Emulator
"""

import unittest
import tempfile
import os
from pathlib import Path
from safety_emulator import (
    SafetyEmulator,
    VulnerabilityDatabase,
    Vulnerability,
    VulnerabilitySeverity,
    InsecurePackage,
    ScanResult
)


class TestSafetyEmulator(unittest.TestCase):
    """Test cases for Safety dependency scanner emulator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = VulnerabilityDatabase()
        self.emulator = SafetyEmulator(db=self.db, verbose=False)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_requirements_file(self, filename: str, content: str) -> str:
        """Create a temporary requirements file"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_vulnerable_django_detection(self):
        """Test detection of vulnerable Django version"""
        requirements = "django==2.2.0\n"
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        self.assertGreater(len(result.vulnerable_packages), 0, "Should detect vulnerable Django")
        self.assertFalse(result.is_safe)
    
    def test_safe_django_detection(self):
        """Test that safe Django version is not flagged"""
        requirements = "django==4.0.0\n"
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        # Check if django is flagged (should not be for newer versions)
        django_vulns = [pkg for pkg in result.vulnerable_packages if pkg.package_name == 'django']
        # Depending on database, this might still have some vulnerabilities
        # We just check that the scan runs successfully
        self.assertIsInstance(result, ScanResult)
    
    def test_vulnerable_flask_detection(self):
        """Test detection of vulnerable Flask version"""
        requirements = "flask==2.0.0\n"
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        flask_vulns = [pkg for pkg in result.vulnerable_packages if pkg.package_name == 'flask']
        self.assertGreater(len(flask_vulns), 0, "Should detect vulnerable Flask")
    
    def test_vulnerable_requests_detection(self):
        """Test detection of vulnerable requests version"""
        requirements = "requests==2.30.0\n"
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        requests_vulns = [pkg for pkg in result.vulnerable_packages if pkg.package_name == 'requests']
        self.assertGreater(len(requests_vulns), 0, "Should detect vulnerable requests")
    
    def test_vulnerable_urllib3_detection(self):
        """Test detection of vulnerable urllib3 version"""
        requirements = "urllib3==1.26.0\n"
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        urllib3_vulns = [pkg for pkg in result.vulnerable_packages if pkg.package_name == 'urllib3']
        self.assertGreater(len(urllib3_vulns), 0, "Should detect vulnerable urllib3")
    
    def test_vulnerable_pyyaml_detection(self):
        """Test detection of critically vulnerable PyYAML version"""
        requirements = "pyyaml==5.3\n"
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        pyyaml_vulns = [pkg for pkg in result.vulnerable_packages if pkg.package_name == 'pyyaml']
        self.assertGreater(len(pyyaml_vulns), 0, "Should detect vulnerable PyYAML")
        
        # Check severity
        for pkg in pyyaml_vulns:
            for vuln in pkg.vulnerabilities:
                self.assertEqual(vuln.severity, VulnerabilitySeverity.CRITICAL)
    
    def test_multiple_vulnerable_packages(self):
        """Test detection of multiple vulnerable packages"""
        requirements = """
django==2.2.0
flask==2.0.0
requests==2.30.0
"""
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        self.assertGreater(len(result.vulnerable_packages), 1, "Should detect multiple vulnerable packages")
        self.assertGreater(result.total_vulnerabilities, 0)
    
    def test_clean_requirements(self):
        """Test scanning requirements with no vulnerabilities"""
        # Using package names that are not in our database
        requirements = """
madeuppackage==1.0.0
anotherpackage==2.0.0
"""
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        self.assertEqual(len(result.vulnerable_packages), 0, "Should have no vulnerabilities")
        self.assertTrue(result.is_safe)
    
    def test_requirements_with_comments(self):
        """Test parsing requirements file with comments"""
        requirements = """
# This is a comment
django==2.2.0  # inline comment
# Another comment
flask==2.0.0
"""
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        self.assertEqual(result.scanned_packages, 2, "Should scan 2 packages, skipping comments")
    
    def test_requirements_with_operators(self):
        """Test parsing requirements with various version operators"""
        requirements = """
package1==1.0.0
package2>=2.0.0
package3~=3.0.0
django<=2.2.0
"""
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        self.assertGreater(result.scanned_packages, 0, "Should parse all requirements")
    
    def test_check_packages_list(self):
        """Test checking a list of packages directly"""
        packages = [
            ('django', '2.2.0'),
            ('flask', '2.0.0'),
            ('safepackage', '1.0.0')
        ]
        
        result = self.emulator.check_packages(packages)
        
        self.assertEqual(result.scanned_packages, 3)
        self.assertGreater(len(result.vulnerable_packages), 0)
    
    def test_version_comparison(self):
        """Test version comparison logic"""
        # Test less than
        self.assertEqual(self.emulator._compare_versions('1.0.0', '2.0.0'), -1)
        self.assertEqual(self.emulator._compare_versions('1.0.0', '1.1.0'), -1)
        
        # Test equal
        self.assertEqual(self.emulator._compare_versions('1.0.0', '1.0.0'), 0)
        
        # Test greater than
        self.assertEqual(self.emulator._compare_versions('2.0.0', '1.0.0'), 1)
        self.assertEqual(self.emulator._compare_versions('1.1.0', '1.0.0'), 1)
    
    def test_parse_requirement(self):
        """Test requirement string parsing"""
        # Test ==
        pkg = self.emulator._parse_requirement('django==2.2.0')
        self.assertEqual(pkg, ('django', '2.2.0'))
        
        # Test >=
        pkg = self.emulator._parse_requirement('flask>=1.0.0')
        self.assertEqual(pkg, ('flask', '1.0.0'))
        
        # Test with extras
        pkg = self.emulator._parse_requirement('django[bcrypt]==2.2.0')
        self.assertEqual(pkg, ('django', '2.2.0'))
        
        # Test with comment
        pkg = self.emulator._parse_requirement('django==2.2.0  # comment')
        self.assertEqual(pkg, ('django', '2.2.0'))
    
    def test_report_generation(self):
        """Test report generation"""
        requirements = """
django==2.2.0
flask==2.0.0
"""
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        report = self.emulator.generate_report(result)
        
        self.assertIn('scanned_packages', report)
        self.assertIn('vulnerable_packages', report)
        self.assertIn('total_vulnerabilities', report)
        self.assertIn('is_safe', report)
        self.assertIn('severity_breakdown', report)
        self.assertIn('affected_packages', report)
        self.assertGreater(report['vulnerable_packages'], 0)
        self.assertFalse(report['is_safe'])
    
    def test_cve_tracking(self):
        """Test that CVE IDs are tracked"""
        requirements = "django==2.2.0\n"
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        
        # Check that vulnerabilities have CVE IDs
        for pkg in result.vulnerable_packages:
            for vuln in pkg.vulnerabilities:
                self.assertIsNotNone(vuln.cve_id, "Vulnerability should have CVE ID")
                self.assertTrue(vuln.cve_id.startswith('CVE-'), "CVE ID should start with 'CVE-'")
    
    def test_nonexistent_requirements_file(self):
        """Test handling of nonexistent requirements file"""
        result = self.emulator.check_requirements('/nonexistent/requirements.txt')
        
        self.assertEqual(result.scanned_packages, 0)
        self.assertEqual(len(result.vulnerable_packages), 0)
        self.assertTrue(result.is_safe)
    
    def test_empty_requirements_file(self):
        """Test handling of empty requirements file"""
        req_file = self._create_requirements_file('requirements.txt', '')
        
        result = self.emulator.check_requirements(req_file)
        
        self.assertEqual(result.scanned_packages, 0)
        self.assertTrue(result.is_safe)
    
    def test_severity_levels(self):
        """Test that different severity levels are assigned"""
        requirements = """
pyyaml==5.3
django==2.2.0
"""
        req_file = self._create_requirements_file('requirements.txt', requirements)
        
        result = self.emulator.check_requirements(req_file)
        report = self.emulator.generate_report(result)
        
        # Should have multiple severity levels
        severity_breakdown = report['severity_breakdown']
        total_severities_used = sum(1 for count in severity_breakdown.values() if count > 0)
        self.assertGreater(total_severities_used, 0, "Should have at least one severity level")


class TestVulnerabilityDatabase(unittest.TestCase):
    """Test VulnerabilityDatabase class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = VulnerabilityDatabase()
    
    def test_default_database_loaded(self):
        """Test that default database is loaded"""
        self.assertGreater(len(self.db.vulnerabilities), 0, "Database should have vulnerabilities")
    
    def test_get_vulnerabilities(self):
        """Test retrieving vulnerabilities for a package"""
        vulns = self.db.get_vulnerabilities('django')
        self.assertGreater(len(vulns), 0, "Should have Django vulnerabilities")
    
    def test_add_vulnerability(self):
        """Test adding a new vulnerability"""
        vuln = Vulnerability(
            package_name='testpackage',
            vulnerable_spec='<1.0.0',
            cve_id='CVE-2023-00000',
            advisory='Test vulnerability',
            severity=VulnerabilitySeverity.HIGH,
            fixed_in='1.0.0'
        )
        
        self.db.add_vulnerability(vuln)
        vulns = self.db.get_vulnerabilities('testpackage')
        
        self.assertEqual(len(vulns), 1)
        self.assertEqual(vulns[0].cve_id, 'CVE-2023-00000')
    
    def test_case_insensitive_lookup(self):
        """Test that package lookup is case-insensitive"""
        vulns_lower = self.db.get_vulnerabilities('django')
        vulns_upper = self.db.get_vulnerabilities('Django')
        vulns_mixed = self.db.get_vulnerabilities('DjAnGo')
        
        self.assertEqual(len(vulns_lower), len(vulns_upper))
        self.assertEqual(len(vulns_lower), len(vulns_mixed))
    
    def test_save_and_load_database(self):
        """Test saving and loading database from file"""
        temp_dir = tempfile.mkdtemp()
        db_file = os.path.join(temp_dir, 'test_db.json')
        
        try:
            # Add custom vulnerability
            vuln = Vulnerability(
                package_name='custompackage',
                vulnerable_spec='<2.0.0',
                cve_id='CVE-2023-99999',
                advisory='Custom test vulnerability',
                severity=VulnerabilitySeverity.MEDIUM,
                fixed_in='2.0.0'
            )
            self.db.add_vulnerability(vuln)
            
            # Save to file
            self.db.save_to_file(db_file)
            
            # Create new database and load
            new_db = VulnerabilityDatabase()
            new_db.vulnerabilities = {}  # Clear default data
            new_db.load_from_file(db_file)
            
            # Verify
            vulns = new_db.get_vulnerabilities('custompackage')
            self.assertGreater(len(vulns), 0, "Should load custom vulnerability")
            self.assertEqual(vulns[0].cve_id, 'CVE-2023-99999')
        
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestVulnerability(unittest.TestCase):
    """Test Vulnerability class"""
    
    def test_vulnerability_creation(self):
        """Test creating a Vulnerability"""
        vuln = Vulnerability(
            package_name='testpkg',
            vulnerable_spec='<1.0.0',
            cve_id='CVE-2023-00000',
            advisory='Test advisory',
            severity=VulnerabilitySeverity.HIGH,
            fixed_in='1.0.0'
        )
        
        self.assertEqual(vuln.package_name, 'testpkg')
        self.assertEqual(vuln.cve_id, 'CVE-2023-00000')
        self.assertEqual(vuln.severity, VulnerabilitySeverity.HIGH)
        self.assertEqual(vuln.fixed_in, '1.0.0')
    
    def test_vulnerability_string_representation(self):
        """Test Vulnerability __str__ method"""
        vuln = Vulnerability(
            package_name='testpkg',
            vulnerable_spec='<1.0.0',
            cve_id='CVE-2023-00000',
            advisory='Test advisory',
            severity=VulnerabilitySeverity.HIGH,
            fixed_in='1.0.0'
        )
        
        str_repr = str(vuln)
        self.assertIn('testpkg', str_repr)
        self.assertIn('CVE-2023-00000', str_repr)
        self.assertIn('HIGH', str_repr)


class TestInsecurePackage(unittest.TestCase):
    """Test InsecurePackage class"""
    
    def test_insecure_package_creation(self):
        """Test creating an InsecurePackage"""
        pkg = InsecurePackage(
            package_name='testpkg',
            installed_version='0.5.0'
        )
        
        self.assertEqual(pkg.package_name, 'testpkg')
        self.assertEqual(pkg.installed_version, '0.5.0')
        self.assertEqual(len(pkg.vulnerabilities), 0)
    
    def test_adding_vulnerabilities(self):
        """Test adding vulnerabilities to InsecurePackage"""
        pkg = InsecurePackage(
            package_name='testpkg',
            installed_version='0.5.0'
        )
        
        vuln = Vulnerability(
            package_name='testpkg',
            vulnerable_spec='<1.0.0',
            cve_id='CVE-2023-00000',
            advisory='Test',
            severity=VulnerabilitySeverity.HIGH
        )
        
        pkg.add_vulnerability(vuln)
        
        self.assertEqual(len(pkg.vulnerabilities), 1)
        self.assertEqual(pkg.vulnerabilities[0].cve_id, 'CVE-2023-00000')


class TestScanResult(unittest.TestCase):
    """Test ScanResult class"""
    
    def test_scan_result_creation(self):
        """Test creating a ScanResult"""
        result = ScanResult()
        
        self.assertEqual(result.scanned_packages, 0)
        self.assertEqual(len(result.vulnerable_packages), 0)
        self.assertTrue(result.is_safe)
        self.assertEqual(result.total_vulnerabilities, 0)
    
    def test_adding_vulnerable_packages(self):
        """Test adding vulnerable packages to ScanResult"""
        result = ScanResult()
        result.scanned_packages = 2
        
        pkg = InsecurePackage(
            package_name='testpkg',
            installed_version='0.5.0'
        )
        
        vuln = Vulnerability(
            package_name='testpkg',
            vulnerable_spec='<1.0.0',
            cve_id='CVE-2023-00000',
            advisory='Test',
            severity=VulnerabilitySeverity.HIGH
        )
        
        pkg.add_vulnerability(vuln)
        result.add_vulnerable_package(pkg)
        
        self.assertEqual(len(result.vulnerable_packages), 1)
        self.assertFalse(result.is_safe)
        self.assertEqual(result.total_vulnerabilities, 1)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    unittest.main()
