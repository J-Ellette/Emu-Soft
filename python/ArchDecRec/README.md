# ArchDecRec - Architecture Decision Record

ADR template system for documenting architecture decisions.

## Usage

```python
from ArchDecRec import ArchDecRec

adr = ArchDecRec()
num = adr.create_adr(
    'Use microservices architecture',
    context='Need better scalability',
    decision='Adopt microservices',
    consequences='Increased complexity but better scaling'
)
markdown = adr.generate_markdown(num)
```

## License

Part of the Emu-Soft project.
