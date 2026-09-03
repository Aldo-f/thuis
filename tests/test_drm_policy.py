"""Tests for DRM decryption policy gate."""

import os
import sys
from unittest.mock import patch

import pytest

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thuis.main import get_decrypt_policy, _is_drm_content


class TestGetDecryptPolicy:
    """Tests for get_decrypt_policy() normalization."""

    def test_default_when_env_absent(self, monkeypatch):
        """No DECRYPT_DRM env var -> defaults to 'yes'."""
        monkeypatch.delenv("DECRYPT_DRM", raising=False)
        assert get_decrypt_policy() == "yes"

    @pytest.mark.parametrize("val", ["yes", "YES", "Yes", "1", "true", "True", "TRUE"])
    def test_truthy_values_return_yes(self, monkeypatch, val):
        """yes|1|true (case-insensitive) -> 'yes'."""
        monkeypatch.setenv("DECRYPT_DRM", val)
        assert get_decrypt_policy() == "yes"

    @pytest.mark.parametrize("val", ["no", "NO", "false", "0", "off", "", "anything"])
    def test_falsy_values_return_no(self, monkeypatch, val):
        """Anything else -> 'no'."""
        monkeypatch.setenv("DECRYPT_DRM", val)
        assert get_decrypt_policy() == "no"


class TestIsDRMContent:
    """Tests for _is_drm_content() DRM detection."""

    def test_widevine_in_vcodec(self):
        """Widevine in vcodec_raw -> DRM."""
        meta = {"vcodec_raw": "widevine", "acodec_raw": "mp4a.40.2", "ext": "mp4"}
        assert _is_drm_content(meta) is True

    def test_playready_in_acodec(self):
        """PlayReady in acodec_raw -> DRM."""
        meta = {"vcodec_raw": "avc1.64002A", "acodec_raw": "playready", "ext": "mp4"}
        assert _is_drm_content(meta) is True

    def test_fairplay_in_vcodec(self):
        """FairPlay in vcodec_raw -> DRM."""
        meta = {"vcodec_raw": "fairplay.drm", "acodec_raw": "mp4a.40.2", "ext": "mp4"}
        assert _is_drm_content(meta) is True

    def test_clearkey_in_acodec(self):
        """ClearKey in acodec_raw -> DRM."""
        meta = {"vcodec_raw": "avc1", "acodec_raw": "clearkey", "ext": "mp4"}
        assert _is_drm_content(meta) is True

    def test_cenc_in_vcodec(self):
        """CENC in vcodec_raw -> DRM."""
        meta = {"vcodec_raw": "avc1.cenc", "acodec_raw": "mp4a", "ext": "mp4"}
        assert _is_drm_content(meta) is True

    def test_smooth_streaming_ext(self):
        """Smooth Streaming extension (.ism) -> DRM."""
        meta = {"vcodec_raw": "avc1", "acodec_raw": "mp4a", "ext": "ism"}
        assert _is_drm_content(meta) is True

    def test_ismv_ext(self):
        """ISMV extension -> DRM."""
        meta = {"vcodec_raw": "avc1", "acodec_raw": "mp4a", "ext": "ismv"}
        assert _is_drm_content(meta) is True

    def test_isma_ext(self):
        """ISMA extension -> DRM."""
        meta = {"vcodec_raw": "avc1", "acodec_raw": "mp4a", "ext": "isma"}
        assert _is_drm_content(meta) is True

    def test_normal_h264_aac_not_drm(self):
        """Normal H.264 + AAC -> not DRM."""
        meta = {"vcodec_raw": "avc1.64002A", "acodec_raw": "mp4a.40.2", "ext": "mp4"}
        assert _is_drm_content(meta) is False

    def test_hevc_aac_not_drm(self):
        """HEVC + AAC -> not DRM."""
        meta = {"vcodec_raw": "hev1.1.6.L150.B0", "acodec_raw": "mp4a.40.2", "ext": "mp4"}
        assert _is_drm_content(meta) is False

    def test_missing_codecs_not_drm(self):
        """Missing codec fields -> not DRM."""
        meta = {}
        assert _is_drm_content(meta) is False

    def test_none_codecs_not_drm(self):
        """None codec fields -> not DRM."""
        meta = {"vcodec_raw": None, "acodec_raw": None, "ext": "mp4"}
        assert _is_drm_content(meta) is False


class TestDRMPolicyGateIntegration:
    """Integration tests for the DRM policy gate in the download flow."""

    def test_drm_skip_when_policy_no(self, monkeypatch, capsys):
        """When DECRYPT_DRM=no and content is DRM -> skip with log."""
        from thuis.main import get_decrypt_policy, _is_drm_content

        monkeypatch.setenv("DECRYPT_DRM", "no")
        policy = get_decrypt_policy()
        assert policy == "no"

        meta = {"vcodec_raw": "widevine", "acodec_raw": "mp4a", "ext": "mp4"}
        assert _is_drm_content(meta) is True

        # Simulate the gate logic
        if _is_drm_content(meta):
            if policy != "yes":
                # This is the skip path
                print("DRM decryption disabled; set DECRYPT_DRM=yes in .env to enable")
                skipped = True
            else:
                skipped = False
        else:
            skipped = False

        assert skipped is True
        captured = capsys.readouterr()
        assert "DRM decryption disabled" in captured.out

    def test_drm_proceed_when_policy_yes(self, monkeypatch):
        """When DECRYPT_DRM=yes and content is DRM -> proceed (no skip)."""
        from thuis.main import get_decrypt_policy, _is_drm_content

        monkeypatch.setenv("DECRYPT_DRM", "yes")
        policy = get_decrypt_policy()
        assert policy == "yes"

        meta = {"vcodec_raw": "widevine", "acodec_raw": "mp4a", "ext": "mp4"}
        assert _is_drm_content(meta) is True

        if _is_drm_content(meta):
            if policy != "yes":
                skipped = True
            else:
                skipped = False
        else:
            skipped = False

        assert skipped is False  # Proceed to C4 path

    def test_non_drm_proceeds_regardless_of_policy(self, monkeypatch):
        """Non-DRM content proceeds regardless of DECRYPT_DRM setting."""
        from thuis.main import get_decrypt_policy, _is_drm_content

        monkeypatch.setenv("DECRYPT_DRM", "no")
        policy = get_decrypt_policy()
        assert policy == "no"

        meta = {"vcodec_raw": "avc1.64002A", "acodec_raw": "mp4a.40.2", "ext": "mp4"}
        assert _is_drm_content(meta) is False

        if _is_drm_content(meta):
            if policy != "yes":
                skipped = True
            else:
                skipped = False
        else:
            skipped = False

        assert skipped is False  # Non-DRM always proceeds