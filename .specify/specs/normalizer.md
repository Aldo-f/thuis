# Filename Normalizer Specification

## Module
`src/thuis/normalizer.py`

## Functions
```python
def normalize_filename(text: str) -> str:
    """
    Normalize a filename to filesystem-safe characters.
    """
```

## Logic
1. Unicode normalize (NFKC)
2. Replace forbidden characters: `<>:"/\|?*` → `_`
3. Strip leading/trailing dots and spaces
4. Collapse multiple underscores/spaces to single `_`
5. Keep only safe ASCII characters (A-Z, a-z, 0-9, `_`, `-`, `.`, ` `)
6. Preserve common accents via transliteration (é → e, etc.)

## Tests
- `tests/thuis/test_normalize.py` (exists)
- Test: special chars, unicode accents, empty string, only dots

## Uses
- Scene naming pipeline
- Watchlist output dir resolution