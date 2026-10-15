"""TDD tests for subtitle flags in build_yt_dlp_args.

These are written BEFORE the implementation exists — they must fail
(ImportError / TypeError) until build_yt_dlp_args gains the
``subtitles_enabled`` parameter and the subtitle flag block.
"""

from pathlib import Path

from thuis.main import build_yt_dlp_args


def test_video_gets_all_subtitles_by_default(tmp_path):
    a = build_yt_dlp_args(
        ["https://www.vrt.be/x"],
        output_dir=tmp_path,
        output_template="Show.S01E01.%(ext)s",
        subtitles_enabled=True,
    )
    assert "--write-subs" in a
    assert a[a.index("--sub-langs") + 1] == "all"
    assert "--convert-subs" not in a  # TTML→VTT handled by transcoder.embed_subtitles()


def test_podcast_never_gets_subtitles(tmp_path):
    a = build_yt_dlp_args(
        ["https://www.vrt.be/x"],
        output_dir=tmp_path,
        output_template="podcast.S01E01.%(ext)s",
        subtitles_enabled=True,
    )
    assert "--write-subs" not in a


def test_subtitles_disabled(tmp_path):
    a = build_yt_dlp_args(
        ["https://www.vrt.be/x"],
        output_dir=tmp_path,
        output_template="Show.S01E01.%(ext)s",
        subtitles_enabled=False,
    )
    assert "--write-subs" not in a