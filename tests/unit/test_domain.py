import pytest

from src.domain.entities.subtitle import Subtitle
from src.domain.entities.video import Video
from src.domain.value_objects.video_id import VideoId


def test_video_id_validation_requires_11_chars() -> None:
    with pytest.raises(ValueError, match="video_id must be 11 characters"):
        VideoId("short")

    valid = VideoId("a" * 11)
    assert str(valid) == "a" * 11


def test_video_creation() -> None:
    video_id = VideoId("b" * 11)
    video = Video(video_id=video_id, source_url="https://youtu.be/12345678901")

    assert video.video_id == video_id
    assert video.source_url == "https://youtu.be/12345678901"
    assert video.subtitles == ()
    assert video.has_embedded_subtitle is False


def test_subtitle_is_translated_property() -> None:
    video_id = VideoId("c" * 11)
    subtitle = Subtitle(
        video_id=video_id,
        language="en",
        format="srt",
        text="Hello",
    )
    translated = Subtitle(
        video_id=video_id,
        language="ko",
        format="srt",
        text="Hello (ko)",
        source_language="en",
    )

    assert subtitle.is_translated is False
    assert translated.is_translated is True
