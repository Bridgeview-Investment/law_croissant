"""
Helper functions for streaming LLM output with markdown formatting.
"""

import sys
import time
from typing import AsyncIterator, Iterator, Optional
try:
    from .streaming_formatter import StreamingFormatter
except ImportError:
    from src.streaming_formatter import StreamingFormatter


class LLMStreamingHelper:
    """Helper class for streaming LLM responses with formatted output."""
    
    def __init__(self, enable_colors: bool = True, typing_delay: float = 0.01):
        """
        Initialize the streaming helper.
        
        Args:
            enable_colors: Whether to enable terminal colors
            typing_delay: Delay between chunks for typing effect (0 for no delay)
        """
        self.formatter = StreamingFormatter(enable_colors)
        self.typing_delay = typing_delay
    
    def stream_response(self, text: str, chunk_size: int = 3):
        """
        Stream a complete response with typing effect.
        
        Args:
            text: The complete text to stream
            chunk_size: Size of each chunk (smaller = slower typing)
        """
        # Reset formatter for new response
        self.formatter.formatter.reset()
        
        # Break text into chunks
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            formatted = self.formatter.formatter.process_chunk(chunk)
            sys.stdout.write(formatted)
            sys.stdout.flush()
            
            if self.typing_delay > 0:
                time.sleep(self.typing_delay)
        
        # Flush any remaining content
        final = self.formatter.formatter.flush()
        if final:
            sys.stdout.write(final)
            sys.stdout.flush()
    
    async def stream_async_response(self, text_stream: AsyncIterator[str]):
        """
        Stream response from an async iterator (e.g., from an LLM API).
        
        Args:
            text_stream: Async iterator yielding text chunks
        """
        # Reset formatter for new response
        self.formatter.formatter.reset()
        
        async for chunk in text_stream:
            formatted = self.formatter.formatter.process_chunk(chunk)
            sys.stdout.write(formatted)
            sys.stdout.flush()
        
        # Flush any remaining content
        final = self.formatter.formatter.flush()
        if final:
            sys.stdout.write(final)
            sys.stdout.flush()
    
    def stream_sync_response(self, text_stream: Iterator[str]):
        """
        Stream response from a sync iterator.
        
        Args:
            text_stream: Iterator yielding text chunks
        """
        # Reset formatter for new response
        self.formatter.formatter.reset()
        
        for chunk in text_stream:
            formatted = self.formatter.formatter.process_chunk(chunk)
            sys.stdout.write(formatted)
            sys.stdout.flush()
        
        # Flush any remaining content
        final = self.formatter.formatter.flush()
        if final:
            sys.stdout.write(final)
            sys.stdout.flush()


def create_streaming_print(enable_colors: bool = True, typing_delay: float = 0.01):
    """
    Create a streaming print function with markdown formatting.
    
    Args:
        enable_colors: Whether to enable terminal colors
        typing_delay: Delay between characters for typing effect
        
    Returns:
        A function that can be used like print() but with streaming and formatting
    """
    helper = LLMStreamingHelper(enable_colors, typing_delay)
    
    def streaming_print(text: str, end: str = '\n'):
        """Print text with streaming and markdown formatting."""
        helper.stream_response(text + end)
    
    return streaming_print


# Example usage for different LLM integrations
class StreamingExamples:
    """Examples of how to integrate with different LLM APIs."""
    
    @staticmethod
    async def openai_streaming_example():
        """Example for OpenAI API streaming (pseudo-code)."""
        # This is pseudo-code showing the pattern
        """
        import openai
        
        helper = LLMStreamingHelper()
        
        # OpenAI streaming response
        response = await openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Explain KYC requirements"}],
            stream=True
        )
        
        async def chunk_generator():
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        await helper.stream_async_response(chunk_generator())
        """
        pass
    
    @staticmethod
    def anthropic_streaming_example():
        """Example for Anthropic API streaming (pseudo-code)."""
        # This is pseudo-code showing the pattern
        """
        import anthropic
        
        helper = LLMStreamingHelper()
        
        # Anthropic streaming response
        client = anthropic.Client()
        
        with client.completion_stream(
            prompt="Explain KYC requirements",
            model="claude-2",
            max_tokens_to_sample=1000,
        ) as stream:
            def chunk_generator():
                for completion in stream:
                    yield completion.completion
            
            helper.stream_sync_response(chunk_generator())
        """
        pass