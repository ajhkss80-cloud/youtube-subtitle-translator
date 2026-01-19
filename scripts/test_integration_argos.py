#!/usr/bin/env python3
"""
Integration test for Argos translation with Clean Architecture use case.
Tests the complete flow from use case through adapter to Argos Translate.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.domain.entities.subtitle import Subtitle
from src.domain.value_objects.video_id import VideoId
from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter
from src.application.use_cases.translate_subtitles import TranslateSubtitlesUseCase


def main():
    print("=" * 60)
    print("Argos Translation Integration Test")
    print("=" * 60)
    print()

    # Create dummy subtitles with proper SRT formatting
    print("Creating test subtitles...")
    video_id = VideoId(value="dQw4w9WgXcQ")  # 11-character YouTube video ID

    # Create properly formatted SRT content
    srt_text_1 = """1
00:00:00,000 --> 00:00:02,000
Hello, how are you?"""

    srt_text_2 = """1
00:00:00,000 --> 00:00:02,000
I am fine, thank you."""

    srt_text_3 = """1
00:00:00,000 --> 00:00:02,000
What is your name?"""

    subtitles = [
        Subtitle(
            video_id=video_id,
            language="en",
            format="srt",
            text=srt_text_1
        ),
        Subtitle(
            video_id=video_id,
            language="en",
            format="srt",
            text=srt_text_2
        ),
        Subtitle(
            video_id=video_id,
            language="en",
            format="srt",
            text=srt_text_3
        ),
    ]

    print(f"Created {len(subtitles)} test subtitles")
    print()

    # Initialize translator adapter and use case
    print("Initializing Argos translator...")
    translator = ArgosTranslatorAdapter()
    use_case = TranslateSubtitlesUseCase(translator)
    print("✓ Translator initialized successfully")
    print()

    # Translate using use case
    target_lang = "ko"

    print(f"Translating to {target_lang}...")
    print("-" * 60)

    try:
        translated_subtitles = []

        # Iterate over each subtitle and translate individually
        for i, subtitle in enumerate(subtitles, 1):
            print(f"Translating subtitle #{i}...")
            translated = use_case.execute(
                subtitle=subtitle,
                target_language=target_lang
            )
            translated_subtitles.append(translated)

        print("✓ Translation completed successfully!")
        print()
        print("Results:")
        print("=" * 60)

        for i, (original, translated) in enumerate(zip(subtitles, translated_subtitles), 1):
            # Extract just the text content (skip number and timestamp lines)
            original_lines = original.text.strip().split('\n')
            original_content = '\n'.join(original_lines[2:]) if len(original_lines) > 2 else original.text

            translated_lines = translated.text.strip().split('\n')
            translated_content = '\n'.join(translated_lines[2:]) if len(translated_lines) > 2 else translated.text

            print(f"\nSubtitle #{i}")
            print(f"  Original (EN): {original_content}")
            print(f"  Translated (KO): {translated_content}")
            print(f"  Source Language: {translated.source_language}")

        print()
        print("=" * 60)
        print("✓ Integration test PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"✗ Translation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
