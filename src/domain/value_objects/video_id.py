"""VideoId - Value Object for YouTube video identifier."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VideoId:
    """YouTube 영상 ID (11자리 고정)"""
    value: str

    def __post_init__(self) -> None:
        v = self.value.strip()
        if not v:
            raise ValueError("video_id cannot be empty")
        if len(v) != 11:
            raise ValueError("video_id must be 11 characters")
    
    def __str__(self) -> str:
        return self.value
