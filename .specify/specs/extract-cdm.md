# Extract CDM Specification

## Module
`src/thuis/extract_cdm.py` — Manual Widevine L3 CDM extraction from rooted Android

## Function
```python
def extract_cdm(
    device_serial: str | None = None,
    output_path: str | None = None,
    package: str = "com.google.android.gms"
) -> str:
    """
    Extract Widevine CDM from rooted Android device via Frida.
    Returns path to saved .wvd file.
    """
```

## Prerequisites
1. Rooted Android device (Magisk/KernelSU)
2. ADB access (`adb shell` as root)
3. Frida server matching device arch (arm64/arm/x86)
4. Python 3.8+ with `frida-tools`, `pywidevine`
5. Frida running on device: `adb shell /data/local/tmp/frida-server &`

## Methods

### Method 1: wvdumper (Recommended)
```bash
# On host
pip install frida-tools

# On device (ADB)
adb push frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell /data/local/tmp/frida-server &

# Clone wvdumper
git clone https://github.com/keyset/wvdumper
cd wvdumper
pip install -r requirements.txt

# Dump CDM
python wvdumper.py -p com.google.android.gms -o my_cdm.wvd

# Pull to host
adb pull /data/local/tmp/my_cdm.wvd ~/.thuis/cdm/widevine_l3_android.wvd
```

### Method 2: Frida Script (Alternative)
```bash
frida -U -f com.google.android.gms -l extract_cdm.js --no-pause
```
Where `extract_cdm.js` hooks `CdmFactory.create()` and dumps device blob.

## Validation
After extraction, validate:
```python
from pywidevine.device import Device
d = Device.load("my_cdm.wvd")
assert d.type == "ANDROID"
assert d.security_level == 3
```

## Xiaomi L1 Note
- Some Xiaomi devices have extractable L1 CDMs (security_level=1)
- pywidevine will reject (validates security_level == 3)
- Not recommended for this tool

## Tests
- `tests/test_extract_cdm.py` (exists — mocks ADB/Frida)
- Test: extraction script generation, output validation

## Warning
- Requires physical device → cannot be auto-fixed by `doctor --fix`
- `doctor` command guides to: `python scripts/extract_cdm.py`