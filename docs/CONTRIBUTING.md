# Contributing to cloudinit-aigen

## Setup
```bash
git clone https://github.com/Ahmedaltu/cloudinit-aigen
cd cloudinit-aigen
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Tests
```bash
pytest tests/ -v
```

## Adding a backend
1. Create `cloudinit_aigen/backends/mybackend.py`
2. Subclass `BaseBackend`, implement `complete(system, user) -> str`
3. Register in `backends/factory.py`

## Adding a validator
1. Add a function to `cloudinit_aigen/tools/validator.py`
2. Call it inside `validate_yaml()`
3. Add tests in `tests/test_validator.py`
