# Task 1 Evidence — Plugin Host

## Files Created
- `src/thuis/plugin_host.py` (86 lines, stdlib only)
- `tests/test_plugin_host.py` (13 tests)

## Test Output
```
$ pytest tests/test_plugin_host.py -v
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /mnt/HDD1/dev/06-apps-thuis-v4
configfile: pyproject.toml
collected 13 items

tests/test_plugin_host.py::TestBaseline::test_entry_points_empty_when_no_plugins PASSED
tests/test_plugin_host.py::TestPostprocessContext::test_frozen_dataclass PASSED
tests/test_plugin_host.py::TestPostprocessContext::test_equality PASSED
tests/test_plugin_host.py::TestPostprocessContext::test_frozen_prevents_reassignment PASSED
tests/test_plugin_host.py::TestLoadEntryPoints::test_returns_list_of_dicts PASSED
tests/test_plugin_host.py::TestLoadEntryPoints::test_empty_entry_points PASSED
tests/test_plugin_host.py::TestPluginManager::test_init_stores_config PASSED
tests/test_plugin_host.py::TestPluginManager::test_load_plugins_no_enabled PASSED
tests/test_plugin_host.py::TestPluginManager::test_load_plugins_empty_enabled_list PASSED
tests/test_plugin_host.py::TestPluginManager::test_load_plugins_filters_by_enabled PASSED
tests/test_plugin_host.py::TestPluginManager::test_run_plugins_calls_each PASSED
tests/test_plugin_host.py::TestPluginManager::test_run_plugins_catches_exception PASSED
tests/test_plugin_host.py::TestPluginManager::test_run_plugins_no_plugins PASSED

============================== 13 passed in 0.20s ==============================
```

## Verification Checklist
- [x] `src/thuis/plugin_host.py` created
- [x] `tests/test_plugin_host.py` created
- [x] `pytest tests/test_plugin_host.py -v` passes (13/13)
- [x] `importlib.metadata.entry_points(group="thuis.postprocess")` returns empty when no plugins installed
- [x] No hardcoded plugin names/paths
- [x] No new dependencies (stdlib only)
- [x] No existing modules modified
- [x] `__all__` export list present
- [x] `logging.getLogger(__name__)` used
- [x] `PostprocessContext` is `@dataclass(frozen=True)`
- [x] Notepads and evidence written

## Notes
- `dict` field in frozen dataclass prevents hashability — expected, not a bug.
- Entry point value format: `"module.path:function_name"` (split on first `:`).
- Plugin config follows nested-dict pattern: `config["plugins"]["enabled"]`.
- Dead code removed: unused `PostprocessFn` Protocol (YAGNI).
