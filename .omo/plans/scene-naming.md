# Scene Naming Conventions voor Thuis Downloader

## TL;DR

> **Quick Summary**: Vervang de huidige `%(title)s.%(ext)s` output template door scene-compliant filenames voor ALLE VRT MAX downloads. Nieuwe modules voor URL parsing, TV/film-classificatie, metadata fetch, en scene-naam builder. Always-on (geen flag), platte directory.
>
> **Deliverables**:
> - `src/thuis/url_parser.py` — URL parsing (show, season, episode)
> - `src/thuis/classifier.py` — TV vs movie vs special detectie
> - `src/thuis/metadata_fetcher.py` — yt-dlp `--print` wrapper + codec mapping
> - `src/thuis/scene_namer.py` — Scene-compliant filename builder
> - Update `src/thuis/main.py` — geïntegreerde pipeline
> - Unit tests voor alle nieuwe modules
> - Update bestaande tests (`test_poc.py`)
> - `pytest` in `requirements.txt`
>
> **Estimated Effort**: Short
> **Parallel Execution**: YES — 3 waves + final verification
> **Critical Path**: url_parser → main.py integratie → E2E test

---

## Context

### Original Request
Gebruiker wil scene naming conventions (torrent/scene standaard) toepassen op gedownloade bestanden van VRT MAX. Geen `%(title)s.%(ext)s` meer, maar `Show.Name.SxxExxx.WEB-DL.Resolution.Audio.Encoding.mp4`.

### Interview Summary
**Key Discussions**:
- **Episode numbering**: E6108 (absoluut, niet relatief per seizoen). >99 cijfers toegestaan, default 2.
- **Name normalization**: spaties → dots, behoud case. "De Zonen van Van As" → `De.Zonen.van.Van.As`
- **Source tag**: `WEB-DL`
- **Bestandsextensie**: `.mp4` (behouden)
- **Episode titel**: NIET in filename, WEL in bestand metadata
- **Always-on**: scene-naming is default, geen `--scene-names` flag
- **--dry-run**: metadata fetch (network) + scene filename tonen
- **Directory**: plat (geen subdirectories per show/seizoen)
- **Specials (geen Sxx/Exx)**: scene-light fallback format
- **TV/movie detectie**: combinatie URL patroon + yt-dlp metadata
- **Fallback**: bij falen → `%(title)s.%(ext)s` (oude gedrag)
- **Per-URL error isolation**: 1 foute URL crashed niet de hele batch

**Research Findings**:
- yt-dlp `--print` metadata: `%(series)s`=show naam ✅, `%(season_number)s`=**NA** (moet uit URL), `%(episode_number)s`=6108 ✅, `%(height)s`=1080, `%(vcodec)s`=avc1.64002A, `%(acodec)s`=mp4a.40.2, `%(ext)s`=mp4
- Codec mapping: `avc1.*`→x264, `hev1.*`/`hvc1.*`→x265, `mp4a.*`→AAC, `ac-3`→AC3
- Bestaande test patterns: pytest + monkeypatch + mock subprocess
- 5 bestaande tests hardcoden `"media/%(title)s.%(ext)s"` — moeten ALLEMAAL geüpdatet worden

### Metis Review
**Identified Gaps** (addressed during interview):
- **Always-on vs opt-in**: Opgelost → always-on (geen flag)
- **Dry-run metadata behavior**: Opgelost → metadata fetch + scene filename tonen
- **Directory structuur**: Opgelost → plat (zoals nu)
- **Season number NA in yt-dlp**: Gedocumenteerd → URL parsing verplicht voor season
- **Codec mapping onbekend**: Geverifieerd met echte yt-dlp output

---

## Work Objectives

### Core Objective
Replace the current `%(title)s.%(ext)s` output template with scene-compliant filenames for all VRT MAX downloads, while preserving all existing features (`--file`, `--dry-run`, `--output-dir`, multi-URL, credentials).

### Concrete Deliverables
- Scene-compliant filenames for TV: `Show.Name.SxxExxx.WEB-DL.Resolution.Audio.Encoding.mp4`
  - Example: `Thuis.S31E6108.WEB-DL.1080p.AAC.x264.mp4`
  - Example: `Ket.Doc.S06E00.WEB-DL.1080p.AAC.x264.mp4` (trailer, no episode → E00)
- Scene-compliant filenames for Movies: `Movie.Title.Year.Resolution.WEB-DL.Audio.Encoding.mp4`
- Scene-light fallback for specials: `Show.Name.Special.WEB-DL.Resolution.Audio.Encoding.mp4`
- Episode title embedded in file metadata (not filename)
- All 4 new modules with unit tests
- Updated existing tests

### Definition of Done
- [x] `python -m pytest tests/ -v` → ALL tests pass (existing + new)
- [ ] `python -m thuis.main --dry-run https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/` → prints `Thuis.S31E6108.WEB-DL.1080p.AAC.x264.mp4`
- [ ] `python -m thuis.main --dry-run https://www.vrt.be/vrtmax/a-z/ket---doc/trailer/ket---doc-trailer-s6/` → prints `Ket.Doc.S00E00.WEB-DL.1080p.AAC.x264.mp4` or similar

### Must Have
- Scene-compliant filenames voor ALLE downloads (always-on)
- TV vs movie auto-classificatie (URL patroon + yt-dlp verificatie)
- URL parsing voor show naam, seizoen, episode (season uit URL omdat yt-dlp NA retourneert)
- Metadata fetch via yt-dlp `--print` voor resolutie/codec info
- Fallback naar `%(title)s.%(ext)s` wanneer scene naming onmogelijk is
- Per-URL error isolation — 1 foute URL crashed niet de hele batch
- Unit tests voor alle nieuwe modules
- Alle bestaande tests blijven slagen (na template update)
- `--dry-run` toont scene filename (doet metadata fetch)
- `--output-dir` blijft werken

### Must NOT Have (Guardrails)
- GEEN `--scene-names` flag (always-on)
- GEEN subdirectories per show/seizoen (plat, zoals nu)
- GEEN episode titel in filename (wel in metadata)
- GEEN andere providers (VRT MAX only)
- GEEN .mkv output (blijf bij .mp4)
- GEEN batch renaming van bestaande downloads
- GEEN database of config file
- GEEN ffmpeg of externe tools voor metadata embedding
- GEEN HDR/Dolby Vision/Atmos flags in filename
- GEEN over-abstractie — modules <200 lines, 1 file per module

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **Automated tests**: YES (tests-after voor bestaande, TDD voor nieuwe)
- **Framework**: pytest
- **Add pytest to requirements**: YES

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Library/Module**: Bash (pytest) — run unit tests, assert pass/fail
- **CLI Integration**: Bash (pytest + Python) — mock subprocess, assert scene filename in -o arg
- **Edge Cases**: Bash (Python) — feed various URL patterns, assert correct outputs

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — MAX parallel: T1 first, T2-T5 depend on VrtUrlInfo type from T1):
├── T1: url_parser.py + tests [quick]
├── T2: classifier.py + tests [quick]
├── T3: scene_namer.py + tests [quick]
├── T4: metadata_fetcher.py + tests (codec mapping) [quick]
└── T5: requirements.txt (add pytest) [quick]

Wave 2 (Integration — depends on W1):
├── T6: Integrate into main.py [deep]
├── T7: Update existing tests (test_poc.py) [quick]
└── T8: --dry-run scene filename display [quick]

Wave 3 (Edge cases + Polish — depends on W2):
├── T9: Edge case handling (specials, fallback, error isolation) [deep]
└── T10: E2E integration test with mocked yt-dlp [quick]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── F1: Plan compliance audit (oracle)
├── F2: Code quality review (unspecified-high)
├── F3: Real QA: run all tests + dry-run check (unspecified-high)
└── F4: Scope fidelity check (deep)
```

### Dependency Matrix
- **T1-T5**: independent — — T6-T8, W2
- **T6**: T1-T5 — T9-T10, W3
- **T7**: T1-T5 (tested modules) — T9, W3
- **T8**: T6 — T9, W3
- **T9**: T6-T8 — T10, W3
- **T10**: T9 — F1-F4, FINAL

---

## TODOs

- [x] 1. **url_parser.py — VRT MAX URL parser**

  **What to do**:
  - Create `src/thuis/url_parser.py` met een `parse_vrt_url(url: str) -> VrtUrlInfo` functie
  - Parsed VRT MAX URL structuur: `/a-z/{show-slug}/{season?}/{show-slug}-s{season}a{episode}/`
  - Haal show slug, season nummer (int), episode nummer (int) eruit
  - `VrtUrlInfo` = typed dict/class met: `show_slug`, `season`, `episode`, `path` (raw path), `url` (original)
  - Normaliseer show slug: spaties → dots, special chars (`&` → `And`), `---` → `-`
  - Normaliseer URL eerst (double slashes strippen, trailing slash)
  - Edge cases: `/extra-s/` (geen season/episode → season=0, episode=0), `/trailer/` (season=0, episode=0)
  - Gebruik `re` (stdlib) voor regex parsing, geen externe dependencies
  - Input: `"https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"`
  - Output: `VrtUrlInfo(show_slug="thuis", season=31, episode=6108)`

  **Must NOT do**:
  - Geen yt-dlp calls in deze module (pure string parsing)
  - Geen generieke URL parser framework bouwen — VRT-specifiek houden
  - Geen try/except rond elke regex match — één exceptie bij parsing failure

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure string parsing met stdlib regex, <100 lines, eenvoudige logica
  - **Skills evaluated but omitted**: None needed (stdlib only)

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5)
  - **Blocks**: Tasks 6, 7 (integration)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `src/thuis/main.py:134-141` — URL deduplication pattern (huidige URL handling)
  - `src/thuis/main.py:89-112` — yt-dlp argument building pattern
  - VRT URL structuur: `/a-z/{show}/{season}/{show}-s{season}a{episode}/`
  - Geteste URL: `https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/` → show=`thuis`, season=`31`, episode=`6108`

  **Acceptance Criteria**:
  - [ ] `url_parser_test.py` aangemaakt met pytest tests
  - [ ] `python -m pytest tests/url_parser_test.py -v` → PASS (>5 tests, 0 failures)

  **QA Scenarios**:
  ```
  Scenario: Parse standard TV episode URL
    Tool: Bash (pytest)
    Preconditions: url_parser.py en url_parser_test.py bestaan
    Steps:
      1. from thuis.url_parser import parse_vrt_url
      2. result = parse_vrt_url("https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/")
      3. assert result.show_slug == "thuis"
      4. assert result.season == 31
      5. assert result.episode == 6108
    Expected Result: All 5 assertions pass
    Evidence: .omo/evidence/task-1-parse-standard.out

  Scenario: Parse special URL (no season/episode)
    Tool: Bash (pytest)
    Preconditions: url_parser.py en url_parser_test.py bestaan
    Steps:
      1. result = parse_vrt_url("https://www.vrt.be/vrtmax/a-z/thuis/extra-s/thuis-wat-vindt-judith-in-de-seizoensfinale/")
      2. assert result.season == 0
      3. assert result.episode == 0
    Expected Result: season=0, episode=0 voor non-standard URLs
    Evidence: .omo/evidence/task-1-parse-special.out

  Scenario: Parse trailer URL
    Tool: Bash (pytest)
    Preconditions: url_parser.py en url_parser_test.py bestaan
    Steps:
      1. result = parse_vrt_url("https://www.vrt.be/vrtmax/a-z/ket---doc/trailer/ket---doc-trailer-s6/")
      2. assert result.season == 0
      3. assert result.episode == 0
    Expected Result: season=0, episode=0 voor trailers
    Evidence: .omo/evidence/task-1-parse-trailer.out

  Scenario: Show slug normalization (special chars)
    Tool: Bash (pytest)
    Preconditions: url_parser.py en url_parser_test.py bestaan
    Steps:
      1. result = parse_vrt_url(".../a-z/ket---doc/trailer/...")  # triple hyphens
      2. assert result.show_slug == "ket-doc"  # normalized
    Expected Result: Triple hyphens → single hyphen in slug
    Evidence: .omo/evidence/task-1-normalize-slug.out
  ```

  **Evidence to Capture**:
  - [ ] pytest output for each scenario
  - [ ] Fout bij onverwachte input (lege string, malformed URL)

  **Commit**: YES
  - Message: `feat(url-parser): add VRT MAX URL parser module`
  - Files: `src/thuis/url_parser.py`, `tests/url_parser_test.py`
  - Pre-commit: `python -m pytest tests/url_parser_test.py -v`

- [x] 2. **classifier.py — TV/movie/special classifier**

  **What to do**:
  - Create `src/thuis/classifier.py` met `classify(vrt_info: VrtUrlInfo, ytdlp_meta: dict | None) -> ContentType`
  - `ContentType` enum: `TV`, `MOVIE`, `SPECIAL`, `UNKNOWN`
  - Classificatie logica:
    1. Check URL path voor patronen: `/extra-s/` → SPECIAL, `/trailer/` → SPECIAL
    2. Check of season > 0 en episode > 0 → TV
    3. Check yt-dlp metadata `%(series)s` — als aanwezig en niet leeg → TV/SPECIAL
    4. Check yt-dlp metadata `%(episode_number)s` — als NA en geen season in URL → MOVIE of SPECIAL
    5. Fallback: UNKNOWN (dan scene-light naming)
  - Gebruik `enum` stdlib (geen externe dep)
  - `ytdlp_meta` is optional dict — classificatie moet ook zonder metadata werken

  **Must NOT do**:
  - Geen machine learning / NLP voor classificatie (binary rules only)
  - Geen generieke content classifier — alleen VRT MAX patronen

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simpele rule-based classifier, <100 lines, geen ML/AI
  - **Skills evaluated but omitted**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5)
  - **Blocks**: Tasks 6, 7
  - **Blocked By**: Task 1 (importeert VrtUrlInfo type)

  **References**:
  - `src/thuis/url_parser.py` (Task 1) — VrtUrlInfo type om te importeren
  - URL patronen: `/extra-s/` = special, `/trailer/` = special, `/seizoen/...` = TV

  **Acceptance Criteria**:
  - [ ] `classifier_test.py` met pytest tests
  - [ ] `python -m pytest tests/classifier_test.py -v` → PASS (≥6 tests)
  - [ ] TV, MOVIE, SPECIAL, UNKNOWN allemaal getest
  - [ ] Classificatie zowel met als zonder yt-dlp metadata

  **QA Scenarios**:
  ```
  Scenario: Classify standard TV URL as TV
    Tool: Bash (pytest)
    Steps:
      1. info = VrtUrlInfo(show_slug="thuis", season=31, episode=6108)
      2. result = classify(info, {"series": "Thuis"})
      3. assert result == ContentType.TV
    Expected: ContentType.TV
    Evidence: .omo/evidence/task-2-classify-tv.out

  Scenario: Classify special URL as SPECIAL
    Tool: Bash (pytest)
    Steps:
      1. info = VrtUrlInfo(show_slug="thuis", season=0, episode=0, path="/extra-s/...")
      2. result = classify(info, None)
      3. assert result == ContentType.SPECIAL
    Expected: ContentType.SPECIAL
    Evidence: .omo/evidence/task-2-classify-special.out

  Scenario: Classify without metadata fallback
    Tool: Bash (pytest)
    Steps:
      1. info = VrtUrlInfo(show_slug="thuis", season=31, episode=6108)
      2. result = classify(info, None)
      3. assert result == ContentType.TV
    Expected: TV op basis van season > 0 alleen
    Evidence: .omo/evidence/task-2-classify-no-meta.out
  ```

  **Evidence to Capture**:
  - [ ] pytest output voor elke scenario
  - [ ] Classificatie met lege/None metadata

  **Commit**: YES (groups with T1)
  - Message: `feat(classifier): add TV/movie/special classifier`
  - Files: `src/thuis/classifier.py`, `tests/classifier_test.py`
  - Pre-commit: `python -m pytest tests/classifier_test.py -v`

- [x] 3. **scene_namer.py — Scene-compliant filename builder**

  **What to do**:
  - Create `src/thuis/scene_namer.py` met:
    - `build_tv_filename(show_name, season, episode, resolution, audio_codec, video_codec) -> str`
    - `build_movie_filename(title, year, resolution, audio_codec, video_codec) -> str`
    - `build_special_filename(show_name, resolution, audio_codec, video_codec) -> str`
  - TV format: `Show.Name.S{season:02d}E{episode:02d}.WEB-DL.{height}p.{audio}.{video}.mp4`
    - Maar: als episode > 99, gebruik `E{episode}` zonder padding (variabele breedte)
    - Voor episode=0 (special/unknown): gebruik `S{season:02d}E00`
  - Movie format: `Movie.Title.{year}.WEB-DL.{height}p.{audio}.{video}.mp4`
  - Special format: `Show.Name.Special.WEB-DL.{height}p.{audio}.{video}.mp4`
  - Show name normalisatie: spaties → dots, verwijder niet-ASCII/niet-alphanumerieke karakters (behalve dots)
  - Gebruik None/leeg voor optionele velden: als resolution onbekend → overslaan
  - `WEB-DL` is hardcoded (VRT MAX is altijd web download)
  - `mp4` is hardcoded extension
  - `CODEC_MAP` centrale dict voor codec lookup: `{"avc1": "x264", "hev1": "x265", "hvc1": "x265", "vp09": "VP9", "av01": "AV1", "mp4a": "AAC", "ac-3": "AC3", "ec-3": "EAC3", "opus": "Opus", "dts": "DTS"}`

  **Must NOT do**:
  - Geen metadata in filename (episode titel hoort in bestand metadata)
  - Geen yt-dlp calls — pure string builder
  - Geen variabele scheidingstekens — altijd periods

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure string formatting, ~120 lines, makkelijk testbaar
  - **Skills evaluated but omitted**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5)
  - **Blocks**: Tasks 6, 8
  - **Blocked By**: None (self-contained)

  **References**:
  - Scene naming format (user opgegeven): `Title.of.show.S00E00.recordingsource.encoding`
  - Codec mapping van yt-dlp velden (gevalideerd): `avc1.64002A` → `x264`, `mp4a.40.2` → `AAC`
  - `re` stdlib voor string normalisatie

  **Acceptance Criteria**:
  - [ ] `scene_namer_test.py` met pytest tests
  - [ ] `python -m pytest tests/scene_namer_test.py -v` → PASS (≥8 tests)
  - [ ] TV, movie, special formats allemaal getest
  - [ ] Episode > 99 werkt (E6108, niet E61)
  - [ ] Codec mapping voor alle ondersteunde codecs
  - [ ] Special characters in show names worden correct genormaliseerd

  **QA Scenarios**:
  ```
  Scenario: Build standard TV filename
    Tool: Bash (pytest)
    Steps:
      1. result = build_tv_filename("Thuis", 31, 6108, "1080", "AAC", "x264")
      2. assert result == "Thuis.S31E6108.WEB-DL.1080p.AAC.x264.mp4"
    Expected: Exact scene-compliant filename
    Evidence: .omo/evidence/task-3-tv-filename.out

  Scenario: Build TV filename with 2-digit episode
    Tool: Bash (pytest)
    Steps:
      1. result = build_tv_filename("Ket & Doc", 6, 5, "1080", "AAC", "x264")
      2. assert result == "Ket.And.Doc.S06E05.WEB-DL.1080p.AAC.x264.mp4"
    Expected: 2-digit episode padding, ampersand → And
    Evidence: .omo/evidence/task-3-tv-2digit.out

  Scenario: Build special filename
    Tool: Bash (pytest)
    Steps:
      1. result = build_special_filename("Thuis", "1080", "AAC", "x264")
      2. assert result == "Thuis.Special.WEB-DL.1080p.AAC.x264.mp4"
    Expected: Special tag
    Evidence: .omo/evidence/task-3-special.out

  Scenario: Build movie filename
    Tool: Bash (pytest)
    Steps:
      1. result = build_movie_filename("Some Movie", 2024, "1080", "AAC", "x264")
      2. assert result == "Some.Movie.2024.WEB-DL.1080p.AAC.x264.mp4"
    Expected: Movie format with year
    Evidence: .omo/evidence/task-3-movie.out

  Scenario: Codec mapping from yt-dlp values
    Tool: Bash (pytest)
    Steps:
      1. result = build_tv_filename("Test", 1, 1, "1080", "mp4a.40.2", "avc1.64002A")
      2. assert result == "Test.S01E01.WEB-DL.1080p.AAC.x264.mp4"
    Expected: Raw yt-dlp codec strings gemapped naar scene labels
    Evidence: .omo/evidence/task-3-codec-mapping.out
  ```

  **Evidence to Capture**:
  - [ ] pytest output voor elke scenario
  - [ ] Codec mapping edge cases (onbekende codec → fallback)

  **Commit**: YES (groups with T1, T2)
  - Message: `feat(scene-namer): add scene-compliant filename builder`
  - Files: `src/thuis/scene_namer.py`, `tests/scene_namer_test.py`
  - Pre-commit: `python -m pytest tests/scene_namer_test.py -v`

- [x] 4. **metadata_fetcher.py — yt-dlp metadata wrapper**

  **What to do**:
  - Create `src/thuis/metadata_fetcher.py` met:
    - `fetch_metadata(url: str, yt_dlp_args: list) -> dict` — roept `yt-dlp --print` aan
    - `parse_codec(vcodec: str) -> str` — map `avc1.64002A` naar `x264`
    - `parse_codec(acodec: str) -> str` — map `mp4a.40.2` naar `AAC`
    - `parse_resolution(height: str) -> str` — map `1080` naar `1080p`
    - `CODEC_MAP` dict (central, ook geïmporteerd door scene_namer)
  - Gebruik `subprocess.run` (consistent met main.py) voor yt-dlp --print
  - Print format: `%(series)s|%(season_number)s|%(episode_number)s|%(height)s|%(vcodec)s|%(acodec)s|%(ext)s|%(title)s`
  - Parse de pipe-gescheiden output terug naar dict
  - Timeout: 60s per metadata call
  - Error handling: bij falen → return leeg dict `{}` (caller valt terug op fallback)
  - Voeg credentials door aan yt-dlp call (zelfde als main.py)

  **Must NOT do**:
  - Geen yt-dlp Python API importeren (blijf bij subprocess, consistent)
  - Geen batch metadata fetch (1 call per URL)
  - Geen complex error handling — gewoon return {} bij falen

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Wrapt subprocess.call, parse output, ~80 lines
  - **Skills evaluated but omitted**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5)
  - **Blocks**: Tasks 6, 8
  - **Blocked By**: None (self-contained, imports alleen stdlib)

  **References**:
  - `src/thuis/main.py:89-112` — build_yt_dlp_args pattern (volgzelfde stijl)
  - `src/thuis/main.py:38-68` — get_yt_dlp_cmd (vind yt-dlp binary)
  - `src/thuis/main.py:107-109` — credentials passing
  - yt-dlp `--print` format: `%(series)s|%(season_number)s|%(episode_number)s|%(height)s|%(vcodec)s|%(acodec)s|%(ext)s`
  - Geteste output: `NA|6108|De politie krijgt...|1080|avc1.64002A|mp4a.40.2|Thuis|mp4`

  **Acceptance Criteria**:
  - [ ] `metadata_fetcher_test.py` met pytest tests (mock subprocess)
  - [ ] `python -m pytest tests/metadata_fetcher_test.py -v` → PASS (≥5 tests)
  - [ ] Codec mapping voor alle ondersteunde codecs
  - [ ] Fallback bij subprocess failure (return {})

  **QA Scenarios**:
  ```
  Scenario: Parse yt-dlp --print output
    Tool: Bash (pytest)
    Steps:
      1. Mock subprocess.run return: stdout = "Thuis|NA|6108|1080|avc1.64002A|mp4a.40.2|mp4"
      2. result = fetch_metadata("https://...", ["yt-dlp"])
      3. assert result["series"] == "Thuis"
      4. assert result["episode"] == 6108
      5. assert result["height"] == 1080
      6. assert result["vcodec_label"] == "x264"
      7. assert result["acodec_label"] == "AAC"
    Expected: Correct parsing en codec mapping
    Evidence: .omo/evidence/task-4-parse-output.out

  Scenario: Handle missing metadata fields
    Tool: Bash (pytest)
    Steps:
      1. Mock subprocess.run return: stdout = "NA|NA|NA|NA|NA|NA|NA"
      2. result = fetch_metadata("https://...", ["yt-dlp"])
      3. assert result["series"] is None
      4. assert result["height"] is None
    Expected: None voor ontbrekende velden
    Evidence: .omo/evidence/task-4-missing-fields.out

  Scenario: Fallback on subprocess failure
    Tool: Bash (pytest)
    Steps:
      1. Mock subprocess.run to raise subprocess.CalledProcessError
      2. result = fetch_metadata("https://...", ["yt-dlp"])
      3. assert result == {}
    Expected: Empty dict, geen crash
    Evidence: .omo/evidence/task-4-fallback.out
  ```

  **Evidence to Capture**:
  - [ ] pytest output voor elke scenario
  - [ ] Codec mapping volledigheid

  **Commit**: YES (groups with T1-T3)
  - Message: `feat(metadata): add yt-dlp metadata fetcher with codec mapping`
  - Files: `src/thuis/metadata_fetcher.py`, `tests/metadata_fetcher_test.py`
  - Pre-commit: `python -m pytest tests/metadata_fetcher_test.py -v`

- [x] 5. **Update requirements.txt — add pytest**

  **What to do**:
  - Voeg `pytest>=8.0` toe aan `requirements.txt`
  - Eventueel `python-dotenv` toevoegen als het nog niet in requirements staat (al gebruikt in main.py)
  - Zorg dat `python -m pytest tests/` werkt vanuit de project root

  **Must NOT do**:
  - Geen dependency versions vastpinnen tenzij noodzakelijk
  - Geen dev/prod split (requirements.txt is de enige dependency file)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single line change in requirements.txt, <1 min werk

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4)
  - **Blocks**: Tasks 6, 7
  - **Blocked By**: None

  **References**:
  - `requirements.txt` — huidige content: 1 regel (yt-dlp fork)
  - `src/thuis/main.py:20-24` — dotenv import (wordt al gebruikt, staat niet in requirements)

  **Acceptance Criteria**:
  - [ ] `pip install -r requirements.txt` installeert pytest
  - [ ] `python -m pytest --version` toont pytest ≥ 8.0

  **QA Scenarios**:
  ```
  Scenario: pytest installed after pip install
    Tool: Bash
    Steps:
      1. pip install -r requirements.txt
      2. python -m pytest --version
    Expected: pytest version ≥ 8.0
    Evidence: .omo/evidence/task-5-pytest-installed.out
  ```

  **Evidence to Capture**:
  - [ ] pytest --version output

  **Commit**: YES (with T1-T4)
  - Message: `chore(deps): add pytest to requirements`
  - Files: `requirements.txt`
  - Pre-commit: `pip install -r requirements.txt && python -m pytest --version`

---

## Wave 2 — Integration

- [x] 6. **Integrate scene naming pipeline into main.py**

  **What to do**:
  - Pas `build_yt_dlp_args()` in `src/thuis/main.py` aan om de scene naming pipeline te gebruiken
  - Nieuwe flow per URL:
    1. Parse URL via `url_parser.parse_vrt_url(url)`
    2. Classificeer via `classifier.classify(vrt_info, metadata)`
    3. Fetch metadata via `metadata_fetcher.fetch_metadata(url, yt_dlp_cmd)`
    4. Bouw scene filename via `scene_namer.build_*_filename(...)`
    5. Gebruik scene filename als output template voor yt-dlp
  - Als een stap faalt: fallback naar `%(title)s.%(ext)s` voor die specifieke URL
  - Per-URL error isolation: try/except per URL in de loop, niet de hele batch
  - **Architectuur keuze**: yt-dlp ondersteunt maar 1 `-o` template per call. Dus elke URL krijgt z'n eigen subprocess call (N calls ipv 1). yt-dlp heeft eenmalige auth overhead, daarna is het snel.
  - Houd alle bestaande features: `--dry-run`, `--file`, `--output-dir`, credentials

  **Must NOT do**:
  - GEEN credentials/email/password wijzigen in de flow
  - GEEN globale state introduceren
  - GEEN yt-dlp Python API importeren — blijf bij subprocess

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core pipeline refactor, threading door bestaande flow, N subprocess calls ipv 1
  - **Skills evaluated but omitted**: None needed

  **Parallelization**:
  - **Can Run In Parallel**: NO (core pipeline change)
  - **Parallel Group**: Wave 2 (sequential within wave)
  - **Blocks**: Tasks 8, 9, 10
  - **Blocked By**: Tasks 1, 2, 3, 4, 5

  **References**:
  - `src/thuis/main.py:89-112` — build_yt_dlp_args (te refactoren)
  - `src/thuis/main.py:151-158` — subprocess.run loop (te refactoren naar per-URL)
  - `src/thuis/url_parser.py` (T1) — URL parsing
  - `src/thuis/classifier.py` (T2) — TV/movie/special detectie
  - `src/thuis/scene_namer.py` (T3) — filename builder
  - `src/thuis/metadata_fetcher.py` (T4) — metadata fetch
  - `src/thuis/main.py:107-109` — credentials passing (ongewijzigd)

  **Acceptance Criteria**:
  - [ ] `python -m thuis.main --dry-run https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/` toont scene filename (geen %(title)s)
  - [ ] `python -m thuis.main --dry-run https://www.vrt.be/vrtmax/a-z/thuis/extra-s/thuis-.../` toont special format
  - [ ] Alle bestaande CLI args werken nog: `--dry-run`, `--file`, `--output-dir`
  - [ ] python -m pytest tests/test_poc.py -v → PASS (na update T7)

  **QA Scenarios**:
  ```
  Scenario: Dry-run prints scene filename for TV episode
    Tool: Bash
    Preconditions: Geen echte download (--dry-run), credentials beschikbaar
    Steps:
      1. python -m thuis.main --dry-run "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"
    Expected: Output toont "Thuis.S31E6108.WEB-DL.1080p.AAC.x264.mp4" of vergelijkbaar
    Evidence: .omo/evidence/task-6-dryrun-tv.out

  Scenario: Dry-run prints scene filename for special
    Tool: Bash
    Steps:
      1. python -m thuis.main --dry-run "https://www.vrt.be/vrtmax/a-z/ket---doc/trailer/ket---doc-trailer-s6/"
    Expected: Output toont scene-light filename (geen %(title)s)
    Evidence: .omo/evidence/task-6-dryrun-special.out

  Scenario: Fallback on unparseable URL
    Tool: Bash (unit test)
    Steps:
      1. Mock url_parser.parse_vrt_url to raise ValueError
      2. Run main() met een test URL
      3. Assert yt-dlp -o argument = "media/%(title)s.%(ext)s"
    Expected: Fallback naar originele template
    Evidence: .omo/evidence/task-6-fallback.out
  ```

  **Evidence to Capture**:
  - [ ] Dry-run output voor TV, special, movie URLs
  - [ ] pytest output voor fallback scenario

  **Commit**: YES
  - Message: `feat(main): integrate scene naming pipeline into download flow`
  - Files: `src/thuis/main.py`
  - Pre-commit: `python -m pytest tests/ -v`

- [x] 7. **Update existing tests in test_poc.py**

  **What to do**:
  - Update 5 bestaande tests in `tests/test_poc.py` die `"media/%(title)s.%(ext)s"` hardcoden
  - De output template verandert naar scene format, dus assertions moeten:
    - Checken dat `-o` argument NIET `%(title)s` bevat
    - Checken dat `-o` argument scene format bevat
    - OF: de scene name builder wordt aangeroepen (test dependency injection)
  - Gebruik `unittest.mock.patch` om de scene naming modules te mocken voor voorspelbare output
  - Behoud alle bestaande test dekking (credentials, file input, dry-run, multi-URL)
  - Voeg nieuwe test: `test_scene_name_appears_in_output` (E2E met gemockte metadata)

  **Must NOT do**:
  - GEEN bestaande tests verwijderen (alleen updaten)
  - GEEN test dekking verminderen

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Update assertions in bestaande tests, voeg 1-2 nieuwe tests toe

  **Parallelization**:
  - **Can Run In Parallel**: NO (hangt samen met T6)
  - **Parallel Group**: Wave 2 (with T6, T8)
  - **Blocks**: Tasks 9, 10
  - **Blocked By**: Tasks 1, 2, 3, 4, 5 (modules moeten bestaan om te mocken)

  **References**:
  - `tests/test_poc.py:45` — `assert called_args[idx_o + 1] == "media/%(title)s.%(ext)s"` (5x)
  - `tests/test_poc.py:75,106,131` — zelfde assertion in andere tests
  - `tests/test_poc.py:16-31` — test_poc_uses_default_credentials (template assertion op regel 45)

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/test_poc.py -v` → ALLE 5 (of meer) tests PASS
  - [ ] Geen enkele test assert nog `"media/%(title)s.%(ext)s"`

  **QA Scenarios**:
  ```
  Scenario: All existing tests pass after update
    Tool: Bash
    Steps:
      1. python -m pytest tests/test_poc.py -v
    Expected: 5 passed (of meer)
    Evidence: .omo/evidence/task-7-all-tests-pass.out

  Scenario: No hardcoded old template in tests
    Tool: Bash (grep)
    Steps:
      1. grep -n "%(title)s.%(ext)s" tests/test_poc.py
    Expected: Geen matches
    Evidence: .omo/evidence/task-7-no-old-template.out
  ```

  **Evidence to Capture**:
  - [ ] pytest output
  - [ ] grep resultaat (geen oude template)

  **Commit**: YES (with T6)
  - Message: `test(update): update existing tests for scene naming output`
  - Files: `tests/test_poc.py`
  - Pre-commit: `python -m pytest tests/test_poc.py -v`

- [x] 8. **Enhance --dry-run to show scene filename**

  **What to do**:
  - In `main.py`: als `--dry-run` actief is, print de scene filenames per URL
  - Format: `[DRY-RUN] Thuis.S31E6108.WEB-DL.1080p.AAC.x264.mp4 <- https://...`
  - Voor elke URL: laat zien wat de scene filename zal zijn
  - Als fallback actief is: toon `[DRY-RUN] (fallback) %(title)s.%(ext)s <- https://...`
  - Behoud `--simulate` in yt-dlp args (voorkomt per ongeluk downloaden)

  **Must NOT do**:
  - GEEN yt-dlp functionaliteit wijzigen (--simulate blijft)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: ~15 lines extra in main.py, print statements

  **Parallelization**:
  - **Can Run In Parallel**: NO (main.py change)
  - **Parallel Group**: Wave 2 (with T6, T7)
  - **Blocks**: Tasks 9, 10
  - **Blocked By**: Task 6 (scene naming pipeline moet bestaan)

  **References**:
  - `src/thuis/main.py:152-158` — huidige subprocess.run met --simulate
  - `src/thuis/main.py:99-101` — dry-run flag handling

  **Acceptance Criteria**:
  - [ ] `python -m thuis.main --dry-run <TV-URL>` print `[DRY-RUN] Show.Name.SxxExxx...`
  - [ ] Fallback URLs printen `[DRY-RUN] (fallback) %(title)s...`

  **QA Scenarios**:
  ```
  Scenario: Dry-run shows scene filename
    Tool: Bash
    Steps:
      1. python -m thuis.main --dry-run "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/" 2>&1 | head -5
    Expected: Output bevat "[DRY-RUN]" en "Thuis.S31E6108"
    Evidence: .omo/evidence/task-8-dryrun.out
  ```

  **Evidence to Capture**:
  - [ ] Dry-run CLI output

  **Commit**: YES (with T6, T7)
  - Message: `feat(cli): enhance --dry-run to show scene filenames`
  - Files: `src/thuis/main.py`
  - Pre-commit: `python -m pytest tests/ -v`

---

## Wave 3 — Edge Cases & Polish

- [x] 9. **Edge case handling & error isolation**

  **What to do**:
  - Zorg voor per-URL error isolation: try/except per URL in de download loop
  - Edge cases:
    - URL met speciale karakters (`&`, `%`, `#`) in show naam
    - URL met double slashes (`//`)
    - yt-dlp metadata fetch timeout (60s timeout al gezet bij T4)
    - Alle metadata velden = NA/None (fallback naar %(title)s)
    - Episode nummer > 999 (E6108 werkt al via T3)
    - Geen network (metadata fetch faalt) → fallback
    - Classifier return UNKNOWN → fallback
  - Zorg dat een foute URL de rest van de batch niet blokkeert
  - Print waarschuwingen voor URLs die naar fallback gaan

  **Must NOT do**:
  - GEEN 15 try/except levels — maximaal 1 try/except per URL
  - GEEN logging framework toevoegen — gewoon print met [WARNING] prefix

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Moet door alle edge cases denken, robuustheid waarborgen

  **Parallelization**:
  - **Can Run In Parallel**: NO (main.py changes)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 10
  - **Blocked By**: Tasks 6, 7, 8

  **References**:
  - `src/thuis/main.py:134-141` — huidige URL dedup (error isolation template)
  - `src/thuis/main.py:151-158` — subprocess.run (error isolation hier toevoegen)
  - `src/thuis/url_parser.py` (T1) — URL normalization

  **Acceptance Criteria**:
  - [ ] `python -m thuis.main --dry-run "valid" "invalid" "valid"` → 2 success, 1 warning
  - [ ] `python -m thuis.main --dry-run "https://vrt.be//bad//url//"` → geen crash
  - [ ] pytest test voor per-URL error isolation

  **QA Scenarios**:
  ```
  Scenario: Bad URL doesn't crash batch
    Tool: Bash (pytest)
    Steps:
      1. Mock: 3 URLs, middle one fails to parse
      2. Run main()
      3. Assert: 2 URLs processed, 1 warning printed
    Expected: Batch completion met warnings
    Evidence: .omo/evidence/task-9-error-isolation.out
  ```

  **Evidence to Capture**:
  - [ ] pytest output

  **Commit**: YES
  - Message: `fix(robustness): add per-URL error isolation and edge case handling`
  - Files: `src/thuis/main.py`, `tests/test_edge_cases.py`
  - Pre-commit: `python -m pytest tests/ -v`

- [x] 10. **E2E integration test with mocked yt-dlp**

  **What to do**:
  - Create `tests/test_integration.py` met volledige pipeline test (alles gemockt)
  - Mock: `subprocess.run` voor metadata fetch + download
  - Test de volledige flow voor:
    - TV URL → scene filename in -o argument
    - Special URL → special format in -o argument
    - Movie URL → movie format in -o argument
    - Fallback URL → %(title)s in -o argument
    - Multi-URL batch (3 URLs) → elk correcte filename
    - --dry-run: print scene filename, geen subprocess download
  - Gebruik `unittest.mock.patch` om metadata_fetcher, url_parser, en subprocess.run te mocken
  - Geen echte network calls of yt-dlp invocations

  **Must NOT do**:
  - GEEN echte yt-dlp calls (blijf mocked)
  - GEEN echte downloads

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Volgt bestaande test patterns (mock subprocess), ~80 lines

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on T9)
  - **Parallel Group**: Wave 3
  - **Blocks**: Nothing (last implementation task)
  - **Blocked By**: Tasks 6, 7, 8, 9

  **References**:
  - `tests/test_poc.py:17` — mock subprocess pattern (MagicMock, returncode)
  - `tests/test_poc.py:78-106` — file input + multi-URL test pattern
  - `src/thuis/main.py:151-158` — te testen pipeline

  **Acceptance Criteria**:
  - [ ] `python -m pytest tests/test_integration.py -v` → PASS (≥5 tests)
  - [ ] Test dekt TV, special, movie, fallback, multi-URL, dry-run

  **QA Scenarios**:
  ```
  Scenario: Full pipeline TV URL produces scene filename
    Tool: Bash (pytest)
    Steps:
      1. Mock url_parser: return VrtUrlInfo("thuis", 31, 6108)
      2. Mock metadata_fetcher: return height=1080, vcodec_label=x264, etc.
      3. Mock subprocess.run for the actual download
      4. Run main()
      5. Assert -o argument contains "Thuis.S31E6108.WEB-DL.1080p.AAC.x264.mp4"
    Expected: Scene filename in final yt-dlp call
    Evidence: .omo/evidence/task-10-e2e-tv.out

  Scenario: Multi-URL batch with mixed types
    Tool: Bash (pytest)
    Steps:
      1. Mock 3 URLs (TV, special, movie)
      2. Run main()
      3. Assert: Each URL produces correct format in its subprocess call
    Expected: Each URL produces correct format
    Evidence: .omo/evidence/task-10-e2e-multi.out
  ```

  **Evidence to Capture**:
  - [ ] pytest output

  **Commit**: YES
  - Message: `test(e2e): add integration test with fully mocked pipeline`
  - Files: `tests/test_integration.py`
  - Pre-commit: `python -m pytest tests/ -v`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run pytest). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.omo/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v` + lint check. Review all changed files for: broad except clauses, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  - [ ] **Fix**: Convert `season_num` and `episode_num` to `int` in `main.py`
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (scene name pipeline working end-to-end). Test edge cases: bad URLs, empty input, special characters. Save to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Task(s) | Commit Message | Files | Pre-commit |
|---------|---------------|-------|------------|
| T1-T4 | `feat(naming): add URL parser, classifier, scene namer, metadata fetcher` | `src/thuis/*.py`, `tests/*_test.py` | `python -m pytest tests/*_test.py -v` |
| T5 | `chore(deps): add pytest to requirements` | `requirements.txt` | `pip install -r requirements.txt && python -m pytest --version` |
| T6-T8 | `feat(main): integrate scene naming, update tests, enhance dry-run` | `src/thuis/main.py`, `tests/test_poc.py` | `python -m pytest tests/test_poc.py -v` |
| T9 | `fix(robustness): add per-URL error isolation and edge case handling` | `src/thuis/main.py`, `tests/test_edge_cases.py` | `python -m pytest tests/ -v` |
| T10 | `test(e2e): add integration test with fully mocked pipeline` | `tests/test_integration.py` | `python -m pytest tests/ -v` |

---

## Success Criteria

### Verification Commands
```bash
# All unit tests pass
python -m pytest tests/ -v

# Dry-run shows scene filename for Thuis episode
python -m thuis.main --dry-run "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"

# Dry-run shows scene-light format for special
python -m thuis.main --dry-run "https://www.vrt.be/vrtmax/a-z/ket---doc/trailer/ket---doc-trailer-s6/"

# --file still works
echo "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/" > /tmp/test_urls.txt
python -m thuis.main --dry-run --file /tmp/test_urls.txt

# -S output dir still works
python -m thuis.main --dry-run --output-dir /tmp/test_output "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"

# Bad URL doesn't crash
python -m thuis.main --dry-run "not-a-url" "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6108/"
```

### Final Checklist
- [ ] All 4 new modules created: url_parser.py, classifier.py, scene_namer.py, metadata_fetcher.py
- [ ] All new modules have unit tests (≥5 tests each)
- [ ] Existing tests updated and passing
- [ ] Integration test covers TV, special, movie, fallback, multi-URL
- [ ] `python -m pytest tests/ -v` → ALL PASS
- [ ] All "Must Have" present, all "Must NOT Have" absent
- [ ] Evidence files in `.omo/evidence/task-*`
- [ ] `--dry-run` toont scene filenames
- [ ] Per-URL error isolation werkt (bad URL crashed niet de batch)
