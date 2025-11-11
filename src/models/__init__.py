"""
🌙 Moon Dev's Model System
Built with love by Moon Dev 🚀
"""

from .base_model import BaseModel, ModelResponse
from .claude_model import ClaudeModel
from .groq_model import GroqModel
from .openai_model import OpenAIModel
# from .gemini_model import GeminiModel  # Temporarily disabled due to protobuf conflict
from .deepseek_model import DeepSeekModel
from .model_factory import get_model_factory

# Lazy-loaded singleton - models only initialize when first accessed
class _LazyModelFactory:
    """Lazy wrapper for model factory - only initializes on first use"""
    _instance = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = get_model_factory()
        return getattr(self._instance, name)

model_factory = _LazyModelFactory()

__all__ = [
    'BaseModel',
    'ModelResponse',
    'ClaudeModel',
    'GroqModel',
    'OpenAIModel',
    # 'GeminiModel',  # Temporarily disabled due to protobuf conflict
    'DeepSeekModel',
    'model_factory'
]