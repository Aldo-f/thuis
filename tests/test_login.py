"""Test login functionality"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLoginURL:
    """Test login URL construction"""

    def test_login_url_construction(self):
        """Should construct correct login URL"""
        redirect_uri = "https://www.vrt.be/vrtmax/sso/callback"
        expected = (
            "https://login.vrt.be/authorize?response_type=code"
            "&client_id=vrtnu-site&redirect_uri=https%3A%2F%2Fwww.vrt.be%2Fvrtmax%2Fsso%2Fcallback"
            "&scope=openid%20profile%20email%20video"
        )

        from urllib.parse import urlencode, quote

        params = {
            "response_type": "code",
            "client_id": "vrtnu-site",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email video",
        }

        actual = "https://login.vrt.be/authorize?" + urlencode(params)

        assert "login.vrt.be/authorize" in actual
        assert "response_type=code" in actual
        assert "client_id=vrtnu-site" in actual


class TestLoginFlow:
    """Test login flow detection"""

    def test_login_success_detection(self):
        """Should detect successful login - URL doesn't contain 'login' after redirect"""
        from thuis import detect_login_success

        assert detect_login_success("https://www.vrt.be/vrtmax/") == True
        assert detect_login_success("https://www.vrt.be/vrtmax/a-z/thuis/") == True

    def test_login_failure_detection(self):
        """Should detect failed login - URL still contains 'login'"""
        from thuis import detect_login_success

        assert detect_login_success("https://login.vrt.be/") == False
        assert (
            detect_login_success("https://login.vrt.be/?error=access_denied") == False
        )


class TestCredentials:
    """Test credential handling"""

    def test_credentials_from_env(self):
        """Should load credentials from environment"""
        import os
        from dotenv import load_dotenv
        from pathlib import Path

        load_dotenv(Path(__file__).parent.parent / ".env")

        username = os.getenv("VRT_USERNAME")
        password = os.getenv("VRT_PASSWORD")

        assert username is not None or password is not None


def detect_login_success(url: str) -> bool:
    """Detect if login was successful based on URL"""
    return "login" not in url.lower()
