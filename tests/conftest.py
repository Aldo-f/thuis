"""Pytest configuration and fixtures"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

VRT_USERNAME = os.getenv("VRT_USERNAME", "")
VRT_PASSWORD = os.getenv("VRT_PASSWORD", "")

TEST_URLS = {
    "drm_free_short": "https://www.vrt.be/vrtmax/a-z/flikken-maastricht/trailer/flikken-maastricht-trailer-s15/",
    "drm_free_long": "https://www.vrt.be/vrtmax/a-z/thuis/31/thuis-s31a6017/",
    "drm_protected": "https://www.vrt.be/vrtmax/a-z/de-camping/1/de-camping-s1a1/",
}


def has_credentials():
    return bool(VRT_USERNAME and VRT_PASSWORD)


skip_no_credentials = pytest.mark.skipif(
    not has_credentials(), reason="Geen VRT credentials gevonden in .env"
)


@pytest.fixture
def vrt_credentials():
    if not has_credentials():
        pytest.skip("Geen VRT credentials")
    return VRT_USERNAME, VRT_PASSWORD


@pytest.fixture
def output_dir():
    output = Path(__file__).parent.parent / "media" / "tests"
    output.mkdir(parents=True, exist_ok=True)
    return output


@pytest.fixture
def test_urls():
    return TEST_URLS
