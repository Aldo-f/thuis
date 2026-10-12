"""TDD tests for subtitle embedding in transcoder.py.

Red phase: these fail with ImportError until the functions exist.
"""
import subprocess
from pathlib import Path
from unittest.mock import patch

from thuis.transcoder import (
    find_subtitle_files,
    video_has_subtitle_stream,
    embed_subtitles,
    _subtitle_lang_tag,
)


def _mk(tmp_path, name):
    p = tmp_path / name
    p.write_bytes(b"x")
    return p


class TestFindSubtitleFiles:
    def test_finds_matching_siblings_only(self, tmp_path):
        v = _mk(tmp_path, "Fc.De.Kampioenen.S03E01.1080p.WEB-DL.mp4")
        _mk(tmp_path, "Fc.De.Kampioenen.S03E01.1080p.WEB-DL.nl.vtt")
        _mk(tmp_path, "Other.S01E01.mp4")
        _mk(tmp_path, "Other.S01E01.nl.vtt")
        names = [f.name for f in find_subtitle_files(v)]
        assert names == ["Fc.De.Kampioenen.S03E01.1080p.WEB-DL.nl.vtt"]

    def test_no_subs(self, tmp_path):
        assert find_subtitle_files(_mk(tmp_path, "Show.mp4")) == []


class TestLangTag:
    def test_nl(self):
        assert _subtitle_lang_tag(Path("a.nl.vtt")) == "nld"

    def test_plain(self):
        assert _subtitle_lang_tag(Path("a.vtt")) == "und"


class TestEmbed:
    def test_no_sub_files_is_success_noop(self, tmp_path):
        ok, err = embed_subtitles(_mk(tmp_path, "Show.mp4"), dry_run=False)
        assert ok and "no subtitle" in err.lower()

    def test_already_embedded_skips_and_cleans(self, tmp_path):
        v = _mk(tmp_path, "Show.mp4")
        _mk(tmp_path, "Show.nl.vtt")
        with patch("thuis.transcoder.video_has_subtitle_stream", return_value=True):
            ok, err = embed_subtitles(v, dry_run=False)
        assert ok and "already" in err.lower()
        assert not (tmp_path / "Show.nl.vtt").exists()

    def test_mux_is_copy_mov_text(self, tmp_path):
            v = _mk(tmp_path, "Show.mp4")
            _mk(tmp_path, "Show.nl.vtt")
            def _fake_run(cmd, *a, **kw):
                # Simulate ffmpeg creating the muxed output file
                Path(cmd[-1]).write_bytes(b"muxed")
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            with patch("thuis.transcoder.video_has_subtitle_stream", return_value=False), \
                 patch("thuis.transcoder.check_ffmpeg", return_value=True), \
                 patch("subprocess.run", side_effect=_fake_run) as m:
                ok, err = embed_subtitles(v, dry_run=False)
            assert ok, err
            cmd = m.call_args[0][0]
            assert "-c" in cmd and "copy" in cmd
            assert "mov_text" in cmd
            assert not (tmp_path / "Show.nl.vtt").exists()

    def test_dry_run_changes_nothing(self, tmp_path):
        v = _mk(tmp_path, "Show.mp4")
        _mk(tmp_path, "Show.nl.vtt")
        with patch("thuis.transcoder.video_has_subtitle_stream", return_value=False):
            ok, err = embed_subtitles(v, dry_run=True)
        assert ok
        assert (tmp_path / "Show.mp4").exists()
        assert (tmp_path / "Show.nl.vtt").exists()
