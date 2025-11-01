# SBOMsAway - SBOM Generator

Generate Software Bill of Materials (SBOM).

## Usage
```python
from SBOMsAway import SBOMsAway
sbom = SBOMsAway()
sbom.add_component('requests', '2.28.0', 'Apache-2.0')
json_sbom = sbom.generate_sbom()
```
