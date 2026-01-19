"""Mock Unit Tests for ArgosTranslatorAdapter."""
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path

import pytest

from src.domain.entities.subtitle import Subtitle
from src.domain.value_objects.video_id import VideoId


@pytest.fixture
def mock_argostranslate():
    """Mock argostranslate module."""
    with patch("src.infrastructure.translators.argos_translator.argostranslate") as mock:
        # Mock package index update
        mock.package.update_package_index = Mock()

        # Mock translator that returns modified string
        mock_translator = Mock()
        mock_translator.translate = Mock(side_effect=lambda text: f"[KO] {text}")

        # Mock installed languages with get_translation method
        mock_lang_en = Mock()
        mock_lang_en.code = "en"
        mock_lang_en.get_translation = Mock(return_value=mock_translator)

        mock_lang_ko = Mock()
        mock_lang_ko.code = "ko"
        mock_lang_ko.get_translation = Mock(return_value=mock_translator)

        mock.translate.get_installed_languages = Mock(return_value=[mock_lang_en, mock_lang_ko])

        yield mock


@pytest.fixture
def sample_subtitle():
    """Create a sample subtitle for testing."""
    srt_content = """1
00:00:00,000 --> 00:00:02,000
Hello World

2
00:00:02,500 --> 00:00:05,000
This is a test subtitle
"""
    return Subtitle(
        video_id=VideoId("test1234567"),
        language="en",
        format="srt",
        text=srt_content,
    )


class TestArgosTranslatorAdapter:
    """ArgosTranslatorAdapter unit tests (with mocks)."""

    def test_initialization(self, mock_argostranslate):
        """Test adapter initialization."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        adapter = ArgosTranslatorAdapter()

        # Verify package index was updated
        mock_argostranslate.package.update_package_index.assert_called_once()

    def test_translate_subtitle_with_text(self, mock_argostranslate, sample_subtitle):
        """Test translating subtitle with text content."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        adapter = ArgosTranslatorAdapter()

        # Execute translation
        result = adapter.translate(sample_subtitle, "ko")

        # Verify result
        assert result.language == "ko"
        assert result.source_language == "en"
        assert "[KO]" in result.text
        assert result.video_id == sample_subtitle.video_id
        assert result.format == sample_subtitle.format

    def test_translate_with_progress_callback(self, mock_argostranslate, sample_subtitle):
        """Test translation with progress callback."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        adapter = ArgosTranslatorAdapter()
        progress_calls = []

        def progress_callback(message: str, percent: float):
            progress_calls.append((message, percent))

        # Execute translation with callback
        adapter.translate(sample_subtitle, "ko", progress_callback=progress_callback)

        # Verify progress was reported
        assert len(progress_calls) > 0
        assert progress_calls[0][1] == 0.0  # First call at 0%
        assert progress_calls[-1][1] == 100.0  # Last call at 100%

    def test_translate_unsupported_language_pair(self, mock_argostranslate, sample_subtitle):
        """Test translation with unsupported language pair."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        # Mock unsupported language pair - get_translation returns None
        mock_lang_en = Mock()
        mock_lang_en.code = "en"
        mock_lang_en.get_translation = Mock(return_value=None)

        mock_argostranslate.translate.get_installed_languages = Mock(return_value=[mock_lang_en])

        adapter = ArgosTranslatorAdapter()

        # Should raise ValueError for unsupported pair
        with pytest.raises(ValueError, match="is not supported"):
            adapter.translate(sample_subtitle, "xyz")

    def test_translate_subtitle_without_text_or_file(self, mock_argostranslate):
        """Test translation with subtitle missing both text and file_path."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        invalid_subtitle = Subtitle(
            video_id=VideoId("test1234567"),
            language="en",
            format="srt",
            text=None,
            file_path=None,
        )

        adapter = ArgosTranslatorAdapter()

        with pytest.raises(ValueError, match="must have either text or file_path"):
            adapter.translate(invalid_subtitle, "ko")

    def test_list_supported_languages(self, mock_argostranslate):
        """Test listing supported languages."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        adapter = ArgosTranslatorAdapter()
        languages = adapter.list_supported_languages()

        # Verify languages are returned and sorted
        assert isinstance(languages, list)
        assert "en" in languages
        assert "ko" in languages
        assert languages == sorted(languages)

    def test_is_language_pair_supported(self, mock_argostranslate):
        """Test checking language pair support."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        adapter = ArgosTranslatorAdapter()

        # Mock supported pair - get_translation returns a translator
        mock_lang_en_supported = Mock()
        mock_lang_en_supported.code = "en"
        mock_lang_en_supported.get_translation = Mock(return_value=Mock())

        mock_lang_ko = Mock()
        mock_lang_ko.code = "ko"

        mock_argostranslate.translate.get_installed_languages = Mock(
            return_value=[mock_lang_en_supported, mock_lang_ko]
        )
        assert adapter.is_language_pair_supported("en", "ko") is True

        # Mock unsupported pair - get_translation returns None
        mock_lang_en_unsupported = Mock()
        mock_lang_en_unsupported.code = "en"
        mock_lang_en_unsupported.get_translation = Mock(return_value=None)

        mock_argostranslate.translate.get_installed_languages = Mock(
            return_value=[mock_lang_en_unsupported]
        )
        assert adapter.is_language_pair_supported("en", "xyz") is False

    def test_parse_srt_cues(self, mock_argostranslate):
        """Test SRT cue parsing."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        adapter = ArgosTranslatorAdapter()

        srt_text = """1
00:00:00,000 --> 00:00:02,000
First subtitle

2
00:00:02,500 --> 00:00:05,000
Second subtitle
Multi-line text
"""

        cues = adapter._parse_srt_cues(srt_text)

        assert len(cues) == 2
        assert cues[0]["number"] == "1"
        assert cues[0]["timestamp"] == "00:00:00,000 --> 00:00:02,000"
        assert cues[0]["text"] == "First subtitle"

        assert cues[1]["number"] == "2"
        assert cues[1]["text"] == "Second subtitle\nMulti-line text"

    def test_reassemble_srt(self, mock_argostranslate):
        """Test SRT reassembly from cues."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        adapter = ArgosTranslatorAdapter()

        cues = [
            {
                "number": "1",
                "timestamp": "00:00:00,000 --> 00:00:02,000",
                "text": "First subtitle",
            },
            {
                "number": "2",
                "timestamp": "00:00:02,500 --> 00:00:05,000",
                "text": "Second subtitle",
            },
        ]

        result = adapter._reassemble_srt(cues)

        assert "1\n00:00:00,000 --> 00:00:02,000\nFirst subtitle" in result
        assert "2\n00:00:02,500 --> 00:00:05,000\nSecond subtitle" in result
        assert result.count("\n\n") >= 1  # Cues separated by blank lines

    def test_initialization_package_index_failure(self, mock_argostranslate):
        """Test adapter initialization when package index update fails."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        # Mock package index update to raise exception
        mock_argostranslate.package.update_package_index = Mock(
            side_effect=Exception("Network error")
        )

        # Should not raise, just print warning
        adapter = ArgosTranslatorAdapter()
        assert adapter is not None

    def test_translate_empty_subtitle_text(self, mock_argostranslate):
        """Test translation with empty subtitle text."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        empty_subtitle = Subtitle(
            video_id=VideoId("test1234567"),
            language="en",
            format="srt",
            text="",
        )

        adapter = ArgosTranslatorAdapter()

        with pytest.raises(ValueError, match="cannot be empty or whitespace only"):
            adapter.translate(empty_subtitle, "ko")

    def test_translate_whitespace_only_subtitle_text(self, mock_argostranslate):
        """Test translation with whitespace-only subtitle text."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        whitespace_subtitle = Subtitle(
            video_id=VideoId("test1234567"),
            language="en",
            format="srt",
            text="   \n\t  ",
        )

        adapter = ArgosTranslatorAdapter()

        with pytest.raises(ValueError, match="cannot be empty or whitespace only"):
            adapter.translate(whitespace_subtitle, "ko")

    def test_translate_no_valid_cues_after_parsing(self, mock_argostranslate):
        """Test translation when no valid cues are found after parsing."""
        from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter

        # Create subtitle with malformed SRT that produces no valid cues
        malformed_subtitle = Subtitle(
            video_id=VideoId("test1234567"),
            language="en",
            format="srt",
            text="This is not a valid SRT format\nJust some random text",
        )

        adapter = ArgosTranslatorAdapter()

        with pytest.raises(ValueError, match="No valid subtitle cues found after parsing"):
            adapter.translate(malformed_subtitle, "ko")
