"""
Asset Generation Service for GamED.AI

- Gemini native (Flash Image) for image generation & editing
- Serper for reference image search
- Pillow for image processing
"""

from .gemini_image import GeminiImageEditor
from .search import ImageSearcher
from .storage import AssetStorage

__all__ = [
    "GeminiImageEditor",
    "ImageSearcher",
    "AssetStorage",
]
