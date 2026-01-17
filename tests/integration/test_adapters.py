import sys
from types import SimpleNamespace

import pytest

from src.domain.entities.subtitle import Subtitle
from src.domain.entities.video import Video
from src.domain.value_objects.video_id import VideoId
from src.infrastructure.downloaders.ytdlp_downloader import YtDlpDownloader
from src.infrastructure.embedders.ffmpeg_embedder import FfmpegEmbedder
from src.infrastructure.extractors.whisper_extractor import WhisperExtractor


def _make_video(tmp_path, name="video.mp4") -> Video:
    video_id = VideoId("a" * 11)
    video_path = tmp_path / name
    video_path.write_text("dummy video", encoding="utf-8")
    return Video(video_id=video_id, source_url="https://youtu.be/aaaaaaaaaaa", file_path=video_path)


def _make_subtitle(tmp_path, video_id, name="subtitle.srt") -> Subtitle:
    subtitle_path = tmp_path / name
    subtitle_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
    return Subtitle(
        video_id=video_id,
        language="en",
        format="srt",
        file_path=subtitle_path,
        source="manual",
    )


def test_ffmpeg_embedder_soft_mode_builds_command(tmp_path, monkeypatch) -> None:
    video = _make_video(tmp_path)
    subtitle = _make_subtitle(tmp_path, video.video_id)
    output_path = tmp_path / "out" / "video.mp4"

    calls = []

    def fake_run(cmd, check=False, capture_output=False, text=False):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("src.infrastructure.embedders.ffmpeg_embedder.subprocess.run", fake_run)

    progress = []

    def progress_callback(message, percent):
        progress.append((message, percent))

    embedder = FfmpegEmbedder()
    result = embedder.embed(
        video=video,
        subtitle=subtitle,
        output_path=output_path,
        mode="soft",
        progress_callback=progress_callback,
    )

    expected_cmd = [
        "ffmpeg", "-y",
        "-i", str(video.file_path),
        "-i", str(subtitle.file_path),
        "-map", "0:v",
        "-map", "0:a",
        "-map", "1:0",
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=en",
        str(output_path),
    ]

    assert result == output_path
    assert output_path.parent.exists()
    assert calls == [expected_cmd]
    assert ("Embedding subtitles (soft)", 0.0) in progress
    assert ("Subtitle embedding complete", 100.0) in progress


def test_ffmpeg_embedder_hard_mode_escapes_subtitle_path(tmp_path, monkeypatch) -> None:
    video = _make_video(tmp_path)
    sub_dir = tmp_path / "sub,dir[1]"
    sub_dir.mkdir(parents=True, exist_ok=True)
    subtitle = _make_subtitle(sub_dir, video.video_id, "sub'.srt")
    output_path = tmp_path / "out" / "hard.mp4"

    calls = []

    def fake_run(cmd, check=False, capture_output=False, text=False):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("src.infrastructure.embedders.ffmpeg_embedder.subprocess.run", fake_run)

    embedder = FfmpegEmbedder()
    embedder.embed(
        video=video,
        subtitle=subtitle,
        output_path=output_path,
        mode="hard",
    )

    escaped = str(subtitle.file_path)
    for char in ["\\", ":", "'", ",", "[", "]"]:
        escaped = escaped.replace(char, f"\\{char}")

    assert calls
    assert calls[0][0:4] == ["ffmpeg", "-y", "-i", str(video.file_path)]
    assert calls[0][4] == "-vf"
    assert f"subtitles={escaped}" in calls[0][5]
    assert "force_style='" in calls[0][5]


def test_ytdlp_downloader_builds_commands_and_resolves_path(tmp_path, monkeypatch) -> None:
    downloader = YtDlpDownloader(yt_dlp_path="yt-dlp")
    url = "https://youtu.be/abcdefghijk"
    # Fallback uses md5(url) if patterns don't match or patterns are limited.
    # The URL matches extract_video_id pattern: "(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})"
    video_id = downloader.extract_video_id(url)
    target_dir = tmp_path / str(video_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    video_path = target_dir / "video.mp4"
    video_path.write_text("dummy video", encoding="utf-8")

    popen_calls = []
    run_calls = []

    class FakeProcess:
        def __init__(self, lines, returncode=0):
            self.stdout = iter(lines)
            self._returncode = returncode

        def wait(self):
            return self._returncode

    def fake_popen(cmd, stdout=None, stderr=None, text=None, bufsize=None):
        popen_calls.append(cmd)
        return FakeProcess(["[download] 12.5% of 1MiB", "done"])

    def fake_run(cmd, check=False, capture_output=False, text=False):
        run_calls.append(cmd)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("src.infrastructure.downloaders.ytdlp_downloader.subprocess.Popen", fake_popen)
    monkeypatch.setattr("src.infrastructure.downloaders.ytdlp_downloader.subprocess.run", fake_run)

    progress = []

    def progress_callback(message, percent):
        progress.append((message, percent))

    video = downloader.download(url=url, output_dir=tmp_path, progress_callback=progress_callback)

    assert popen_calls
    # assert run_calls  <-- YtDlpDownloader now uses Popen only
    assert popen_calls[0][0] == "yt-dlp"
    assert "--format" in popen_calls[0]
    assert "--merge-output-format" in popen_calls[0]
    assert "--output" in popen_calls[0]
    assert url in popen_calls[0]
    assert video.file_path == video_path
    assert any(percent == 12.5 for _, percent in progress)


def test_whisper_extractor_writes_srt_with_mocked_model(tmp_path, monkeypatch) -> None:
    video = _make_video(tmp_path)
    output_path = tmp_path / "subs" / "out.srt"

    class FakeModel:
        def transcribe(self, path, **kwargs):
            return {
                "segments": [
                    {"start": 0.0, "end": 1.0, "text": "Hello world"},
                ]
            }

    load_calls = []

    def fake_load_model(model_name):
        load_calls.append(model_name)
        return FakeModel()

    fake_whisper = SimpleNamespace(load_model=fake_load_model)
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    progress = []

    def progress_callback(message, percent):
        progress.append((message, percent))

    extractor = WhisperExtractor(model_name="tiny")
    subtitle = extractor.extract(
        video=video,
        output_path=output_path,
        language="en",
        progress_callback=progress_callback,
    )

    assert output_path.exists()
    contents = output_path.read_text(encoding="utf-8")
    assert "Hello world" in contents
    assert subtitle.file_path == output_path
    assert subtitle.source == "whisper"
    assert load_calls == ["tiny"]
    assert ("Generating subtitles with Whisper (tiny)...", 0.0) in progress
    assert ("Subtitle ready", 100.0) in progress
