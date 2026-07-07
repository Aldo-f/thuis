# Draft: Clean KeyboardInterrupt handling

## Problem
Bij Ctrl+C tijdens GraphQL/HEAD network calls krijg je een lelijke traceback doordat `KeyboardInterrupt` onbehandeld door de call stack heen schiet, met name:
1. In `_execute_graphql_query()` — `urllib.request.urlopen()` wordt onderbroken
2. In `_guess_episode_urls()` — HEAD requests worden onderbroken

## Root Cause
- De URL-expansie fase (lines 796-820 in `main()`) valt **buiten** beide `try/except KeyboardInterrupt` blokken
- `_execute_graphql_query()` heeft geen specifieke `except KeyboardInterrupt` vóór de generieke `except Exception`
- De paginatieloops hebben geen interrupt-aware break-mechanisme

## Proposed Fixes
1. `_execute_graphql_query()` — vang KeyboardInterrupt specifiek, return None
2. `_guess_episode_urls()` — vang KeyboardInterrupt in while-loop, break
3. `fetch_all_seasons()` — vang KeyboardInterrupt in season-loop, break en return partial results
4. `main()` — wrap URL-expansie in try/except KeyboardInterrupt

## Test Strategy
- N.v.t. — dit is een runtime UX verbetering, geen functionele verandering
- QA scenario: Ctrl+C tijdens GraphQL pagination moet clean stoppen zonder traceback
