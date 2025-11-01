# ChangeLogGen - Changelog Generator

Generate changelogs from git commits.

## Usage

```python
from ChangeLogGen import ChangeLogGen

gen = ChangeLogGen()
gen.add_commit('abc123', 'feat: add new feature')
changelog = gen.generate_changelog('1.0.0')
```

## License

Part of the Emu-Soft project.
