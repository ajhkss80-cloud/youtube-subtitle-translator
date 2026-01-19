"""Unit Tests for TranslateSubtitlesUseCase."""
from unittest.mock import Mock

import pytest

from src.application.ports.subtitle_translator import SubtitleTranslatorPort
from src.application.use_cases.translate_subtitles import TranslateSubtitlesUseCase
from src.domain.entities.subtitle import Subtitle
from src.domain.value_objects.video_id import VideoId


class FakeSubtitleTranslator(SubtitleTranslatorPort):
    """Fake translator for testing."""

    def __init__(self):
        self.translate_called = False
        self.translate_args = None
        self.should_raise = None

    def translate(self, subtitle, target_language, progress_callback=None):
        self.translate_called = True
        self.translate_args = (subtitle, target_language, progress_callback)

        if self.should_raise:
            raise self.should_raise

        # Return translated subtitle
        return subtitle.with_translation(
            f"[Translated to {target_language}] {subtitle.text}",
            target_language,
        )

    def list_supported_languages(self):
        return ["en", "ko", "ja", "zh"]

    def is_language_pair_supported(self, source_language, target_language):
        return target_language in ["en", "ko", "ja", "zh"]


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


class TestTranslateSubtitlesUseCase:
    """TranslateSubtitlesUseCase unit tests."""

    def test_execute_basic_translation(self, sample_subtitle):
        """Test basic translation execution."""
        fake_translator = FakeSubtitleTranslator()
        use_case = TranslateSubtitlesUseCase(fake_translator)

        result = use_case.execute(sample_subtitle, "ko")

        # Verify translator was called
        assert fake_translator.translate_called
        assert fake_translator.translate_args[0] == sample_subtitle
        assert fake_translator.translate_args[1] == "ko"

        # Verify result
        assert result.language == "ko"
        assert result.source_language == "en"
        assert "[Translated to ko]" in result.text

    def test_execute_with_progress_callback(self, sample_subtitle):
        """Test translation with progress callback."""
        fake_translator = FakeSubtitleTranslator()
        use_case = TranslateSubtitlesUseCase(fake_translator)

        progress_calls = []

        def progress_callback(message: str, percent: float):
            progress_calls.append((message, percent))

        result = use_case.execute(sample_subtitle, "ja", progress_callback=progress_callback)

        # Verify callback was passed to translator
        assert fake_translator.translate_args[2] == progress_callback

        # Verify translation succeeded
        assert result.language == "ja"

    def test_execute_validates_source_subtitle(self):
        """Test that source subtitle is validated before translation."""
        fake_translator = FakeSubtitleTranslator()
        use_case = TranslateSubtitlesUseCase(fake_translator)

        # Create invalid subtitle (empty language)
        invalid_subtitle = Subtitle(
            video_id=VideoId("test1234567"),
            language="",  # Invalid empty language
            format="srt",
            text="Some text",
        )

        # Should raise validation error
        with pytest.raises(ValueError, match="language cannot be empty"):
            use_case.execute(invalid_subtitle, "ko")

        # Translator should not have been called
        assert not fake_translator.translate_called

    def test_execute_validates_translated_subtitle(self, sample_subtitle):
        """Test that translated subtitle is validated after translation."""
        fake_translator = FakeSubtitleTranslator()

        # Make translator return invalid subtitle
        def bad_translate(subtitle, target_language, progress_callback=None):
            return Subtitle(
                video_id=subtitle.video_id,
                language="",  # Invalid empty language
                format=subtitle.format,
                text=subtitle.text,
            )

        fake_translator.translate = bad_translate

        use_case = TranslateSubtitlesUseCase(fake_translator)

        # Should raise validation error for result
        with pytest.raises(ValueError, match="language cannot be empty"):
            use_case.execute(sample_subtitle, "ko")

    def test_execute_propagates_translation_errors(self, sample_subtitle):
        """Test that translation errors are propagated."""
        fake_translator = FakeSubtitleTranslator()
        fake_translator.should_raise = RuntimeError("Translation engine failed")

        use_case = TranslateSubtitlesUseCase(fake_translator)

        # Should propagate the translation error
        with pytest.raises(RuntimeError, match="Translation engine failed"):
            use_case.execute(sample_subtitle, "ko")

    def test_execute_propagates_value_errors(self, sample_subtitle):
        """Test that ValueError from translator is propagated."""
        fake_translator = FakeSubtitleTranslator()
        fake_translator.should_raise = ValueError("Unsupported language pair")

        use_case = TranslateSubtitlesUseCase(fake_translator)

        # Should propagate the ValueError
        with pytest.raises(ValueError, match="Unsupported language pair"):
            use_case.execute(sample_subtitle, "xyz")

    def test_multiple_translations(self, sample_subtitle):
        """Test multiple consecutive translations."""
        fake_translator = FakeSubtitleTranslator()
        use_case = TranslateSubtitlesUseCase(fake_translator)

        # First translation: en -> ko
        result1 = use_case.execute(sample_subtitle, "ko")
        assert result1.language == "ko"
        assert result1.source_language == "en"

        # Second translation: ko -> ja (translating the translated subtitle)
        result2 = use_case.execute(result1, "ja")
        assert result2.language == "ja"
        assert result2.source_language == "ko"  # Previous language

    def test_subtitle_immutability(self, sample_subtitle):
        """Test that original subtitle is not modified."""
        fake_translator = FakeSubtitleTranslator()
        use_case = TranslateSubtitlesUseCase(fake_translator)

        original_language = sample_subtitle.language
        original_text = sample_subtitle.text

        # Execute translation
        result = use_case.execute(sample_subtitle, "ko")

        # Verify original is unchanged
        assert sample_subtitle.language == original_language
        assert sample_subtitle.text == original_text
        assert sample_subtitle.source_language is None

        # Verify result is different
        assert result.language == "ko"
        assert result.source_language == "en"
        assert result is not sample_subtitle


class TestTranslateSubtitlesUseCaseIntegration:
    """Integration-style tests with more realistic scenarios."""

    def test_translation_preserves_metadata(self, sample_subtitle):
        """Test that video_id and format are preserved."""
        fake_translator = FakeSubtitleTranslator()
        use_case = TranslateSubtitlesUseCase(fake_translator)

        result = use_case.execute(sample_subtitle, "ko")

        assert result.video_id == sample_subtitle.video_id
        assert result.format == sample_subtitle.format

    def test_translation_with_none_progress_callback(self, sample_subtitle):
        """Test that None progress_callback is handled correctly."""
        fake_translator = FakeSubtitleTranslator()
        use_case = TranslateSubtitlesUseCase(fake_translator)

        # Should not raise error with None callback
        result = use_case.execute(sample_subtitle, "ko", progress_callback=None)

        assert result.language == "ko"
        assert fake_translator.translate_args[2] is None
