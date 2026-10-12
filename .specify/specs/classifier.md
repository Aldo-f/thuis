# Content Classifier Specification

## Module
`src/thuis/classifier.py`

## Function
```python
class ContentType(Enum):
    TV_SHOW = "TV_SHOW"
    MOVIE = "MOVIE"
    PODCAST = "PODCAST"
    UNKNOWN = "UNKNOWN"

def classify(vrt_info: VRTInfo, metadata: dict) -> ContentType:
    """
    Classify content based on URL info + metadata.
    Uses keyword detection in metadata['title'] for:
    - "film", "movie", "documentaire" → MOVIE
    - "podcast" → PODCAST
    - otherwise → TV_SHOW
    """
```

## Logic
1. If `metadata.title` contains "podcast" (case-insensitive) → PODCAST
2. If `metadata.title` contains "film" or "movie" or "documentaire" → MOVIE
3. If `vrt_info.content_type == 'show'` → TV_SHOW
4. Otherwise → UNKNOWN

## Tests
- `tests/classifier_test.py` (exists — verify coverage matches spec)

## Key Test Cases
| Input | Expected |
|-------|----------|
| title="De Film van..." | MOVIE |
| title="Podcast X" | PODCAST |
| title="Thuis" + show URL | TV_SHOW |
| title="Random Video" | UNKNOWN |