"""
Qwen Model Implementation (Alibaba Cloud)
Built with love by Moon Dev

Qwen API is OpenAI-compatible, making integration straightforward
"""

from openai import OpenAI
from termcolor import cprint
from .base_model import BaseModel
import random

class QwenModel(BaseModel):
    """Qwen model implementation using OpenAI-compatible API"""

    # Available Qwen models
    AVAILABLE_MODELS = {
        "qwen-max": "qwen-max-2025-01-25",  # Latest Qwen Max model (most powerful)
        "qwen-plus": "qwen-plus",  # Balanced performance
        "qwen-turbo": "qwen-turbo",  # Fast and efficient
        "qwen-long": "qwen-long",  # Extended context (1M tokens)
        "qwen-coder": "qwen-coder-turbo",  # Specialized for coding
    }

    def __init__(self, api_key: str, model_name: str = "qwen-max-2025-01-25"):
        """
        Initialize Qwen model

        Args:
            api_key: Alibaba Cloud API key (DashScope API Key)
            model_name: Model to use (default: qwen-max-2025-01-25)
        """
        super().__init__(api_key, model_name)

        cprint("\nInitializing Qwen Model...", "cyan")
        cprint(f"Model: {model_name}", "cyan")

        # Qwen uses OpenAI-compatible API with custom base URL
        self.base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
            cprint("Qwen client initialized successfully", "green")

        except Exception as e:
            cprint(f"Failed to initialize Qwen client: {str(e)}", "red")
            raise

    def is_available(self) -> bool:
        """Check if Qwen model is available"""
        try:
            # Test with a simple request
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return response is not None

        except Exception as e:
            cprint(f"Qwen model not available: {str(e)}", "yellow")
            return False

    def generate_response(self, system_prompt, user_content, temperature=0.7, max_tokens=None):
        """
        Generate a response from Qwen

        Args:
            system_prompt: System instructions
            user_content: User message
            temperature: Randomness (0.0-1.0)
            max_tokens: Max tokens to generate

        Returns:
            Response object with .content attribute
        """
        try:
            # Add random nonce to prevent caching (same pattern as other models)
            nonce = f"_{random.randint(1, 1000000)}"

            cprint(f"\nGenerating response with Qwen ({self.model_name})...", "cyan")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_content}{nonce}"}
                ],
                temperature=temperature,
                max_tokens=max_tokens if max_tokens else self.max_tokens
            )

            cprint("Response generated successfully", "green")
            return response.choices[0].message

        except Exception as e:
            if "503" in str(e):
                cprint("Qwen service temporarily unavailable (503), retrying...", "yellow")
                raise e  # Let retry logic handle 503s

            cprint(f"Qwen model error: {str(e)}", "red")
            return None

    def get_model_info(self):
        """Get information about the current model"""
        return {
            "provider": "Qwen (Alibaba Cloud)",
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "base_url": self.base_url,
            "api_compatible": "OpenAI",
            "features": self._get_model_features()
        }

    def _get_model_features(self):
        """Get features specific to the current model"""
        features = {
            "qwen-max-2025-01-25": {
                "description": "Most powerful Qwen model with enhanced reasoning",
                "context_window": 32000,
                "strengths": ["Complex reasoning", "Code generation", "Trading analysis"]
            },
            "qwen-plus": {
                "description": "Balanced performance and cost",
                "context_window": 32000,
                "strengths": ["General tasks", "Analysis", "Content generation"]
            },
            "qwen-turbo": {
                "description": "Fast and efficient for high-volume tasks",
                "context_window": 8000,
                "strengths": ["Quick responses", "Simple tasks", "High throughput"]
            },
            "qwen-long": {
                "description": "Extended context window for long documents",
                "context_window": 1000000,
                "strengths": ["Long documents", "Research", "Comprehensive analysis"]
            },
            "qwen-coder-turbo": {
                "description": "Specialized for code generation and analysis",
                "context_window": 32000,
                "strengths": ["Code generation", "Debugging", "Backtesting strategies"]
            }
        }

        return features.get(self.model_name, {
            "description": "Qwen model",
            "context_window": 32000,
            "strengths": ["General tasks"]
        })


# Example usage and testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('QWEN_API_KEY')

    if not api_key:
        cprint("QWEN_API_KEY not found in .env file", "red")
        exit(1)

    # Test Qwen Max (most powerful)
    cprint("\nTesting Qwen Max...", "cyan")
    model = QwenModel(api_key, "qwen-max-2025-01-25")

    # Display model info
    info = model.get_model_info()
    cprint("\nModel Information:", "cyan")
    for key, value in info.items():
        cprint(f"  {key}: {value}", "yellow")

    # Test generation
    response = model.generate_response(
        system_prompt="You are an expert trading analyst.",
        user_content="Explain the benefits of using AI for algorithmic trading in one paragraph.",
        temperature=0.7,
        max_tokens=200
    )

    if response:
        cprint("\nResponse:", "green")
        cprint(response.content, "white")

    # Test Qwen Coder (for code generation)
    cprint("\n\nTesting Qwen Coder...", "cyan")
    coder = QwenModel(api_key, "qwen-coder-turbo")

    code_response = coder.generate_response(
        system_prompt="You are an expert Python developer specializing in trading algorithms.",
        user_content="Write a simple moving average crossover function in Python.",
        temperature=0.3,
        max_tokens=300
    )

    if code_response:
        cprint("\nCode Response:", "green")
        cprint(code_response.content, "white")

    cprint("\n\nQwen model tests complete!", "green")
