"""
Streaming terminal formatter for LLM output.
Handles markdown formatting in a streaming context where text arrives in chunks.
"""

import re
from typing import Optional, Tuple
try:
    from .terminal_formatter import TerminalFormatter
except ImportError:
    from src.terminal_formatter import TerminalFormatter


class StreamingTerminalFormatter(TerminalFormatter):
    """
    A terminal formatter that supports streaming text processing.
    Maintains state between chunks to handle markdown syntax that spans multiple chunks.
    """
    
    def __init__(self, enable_colors: bool = True):
        """Initialize the streaming formatter with state tracking."""
        super().__init__(enable_colors)
        self.reset()
    
    def reset(self):
        """Reset the formatter state for a new streaming session."""
        self.buffer = ""  # Buffer for incomplete markdown syntax
        self.in_bold = False
        self.in_italic = False
        self.in_code = False
        self.in_code_block = False
        self.code_block_lang = ""
        self.pending_header = ""
        self.line_buffer = ""  # Buffer for incomplete lines
    
    def process_chunk(self, chunk: str) -> str:
        """
        Process a chunk of streaming text and return formatted output.
        
        Args:
            chunk: A chunk of text from the LLM stream
            
        Returns:
            Formatted text that can be immediately displayed
        """
        if not self.enable_colors:
            return chunk
        
        # Add chunk to line buffer
        self.line_buffer += chunk
        
        # Process complete lines and keep incomplete line in buffer
        lines = self.line_buffer.split('\n')
        complete_lines = lines[:-1]
        self.line_buffer = lines[-1]
        
        formatted_output = []
        
        for i, line in enumerate(complete_lines):
            # Add newline back except for the last line if there's no remaining buffer
            if i < len(complete_lines) - 1 or self.line_buffer:
                line += '\n'
            formatted_line = self._process_line(line, is_complete=True)
            formatted_output.append(formatted_line)
        
        # Process the incomplete line (if any)
        if self.line_buffer:
            partial_formatted = self._process_line(self.line_buffer, is_complete=False)
            formatted_output.append(partial_formatted)
        
        return ''.join(formatted_output)
    
    def _process_line(self, text: str, is_complete: bool) -> str:
        """Process a single line or partial line of text."""
        output = []
        i = 0
        
        while i < len(text):
            # Check for code blocks first (highest priority)
            if not self.in_code_block and text[i:i+3] == '```':
                # Start or end code block
                if self.in_code_block:
                    self.in_code_block = False
                    self.code_block_lang = ""
                    i += 3
                    continue
                else:
                    # Look for language specification
                    self.in_code_block = True
                    i += 3
                    # Extract language if present
                    lang_match = re.match(r'([a-zA-Z]+)\n', text[i:])
                    if lang_match:
                        self.code_block_lang = lang_match.group(1)
                        i += len(lang_match.group(0))
                    continue
            
            # If we're in a code block, format accordingly
            if self.in_code_block:
                if text[i] == '\n':
                    output.append('\n')
                else:
                    # Apply code block formatting to each character
                    if not output or output[-1] == '\n':
                        output.append(f"{self.COLORS['BG_GRAY']}{self.COLORS['BRIGHT_WHITE']}")
                    output.append(text[i])
                    if i + 1 >= len(text) or text[i + 1] == '\n':
                        output.append(self.COLORS['RESET'])
                i += 1
                continue
            
            # Check for headers at line start
            if i == 0 and is_complete:
                header_match = re.match(r'^(#{1,4})\s+', text)
                if header_match:
                    level = len(header_match.group(1))
                    header_text = text[header_match.end():]
                    if level == 1:
                        return f"{self.COLORS['BLUE']}{self.COLORS['BOLD']}{self.COLORS['UNDERLINE']}{header_text}{self.COLORS['RESET']}"
                    elif level == 2:
                        return f"{self.COLORS['GREEN']}{self.COLORS['BOLD']}{header_text}{self.COLORS['RESET']}"
                    elif level == 3:
                        return f"{self.COLORS['YELLOW']}{self.COLORS['BOLD']}{header_text}{self.COLORS['RESET']}"
                    elif level == 4:
                        return f"{self.COLORS['CYAN']}{self.COLORS['BOLD']}{header_text}{self.COLORS['RESET']}"
            
            # Check for bold syntax
            if text[i:i+2] == '**':
                if self.in_bold:
                    output.append(self.COLORS['RESET'])
                    self.in_bold = False
                else:
                    output.append(self.COLORS['BOLD'])
                    self.in_bold = True
                i += 2
                continue
            
            # Check for italic syntax (single asterisk, not part of bold)
            if text[i] == '*' and (i + 1 >= len(text) or text[i+1] != '*') and (i == 0 or text[i-1] != '*'):
                if self.in_italic:
                    output.append(self.COLORS['RESET'])
                    self.in_italic = False
                else:
                    output.append(self.COLORS['DIM'])
                    self.in_italic = True
                i += 1
                continue
            
            # Check for inline code
            if text[i] == '`':
                if self.in_code:
                    output.append(self.COLORS['RESET'])
                    self.in_code = False
                else:
                    output.append(f"{self.COLORS['BG_GRAY']}{self.COLORS['WHITE']}")
                    self.in_code = True
                i += 1
                continue
            
            # Regular character
            output.append(text[i])
            i += 1
        
        # Don't close formatting if line is incomplete and might continue
        if is_complete:
            # Reset any open formatting at line end
            if self.in_bold:
                output.append(self.COLORS['RESET'])
                self.in_bold = False
            if self.in_italic:
                output.append(self.COLORS['RESET'])
                self.in_italic = False
            if self.in_code:
                output.append(self.COLORS['RESET'])
                self.in_code = False
        
        return ''.join(output)
    
    def flush(self) -> str:
        """
        Flush any remaining buffered content and reset state.
        Call this when the stream is complete.
        
        Returns:
            Any remaining formatted text
        """
        if self.line_buffer:
            formatted = self._process_line(self.line_buffer, is_complete=True)
            self.reset()
            return formatted
        self.reset()
        return ""


class StreamingFormatter:
    """
    A simpler streaming formatter for real-time LLM output.
    Formats text character by character as it arrives.
    """
    
    def __init__(self, enable_colors: bool = True):
        self.enable_colors = enable_colors
        self.formatter = StreamingTerminalFormatter(enable_colors)
    
    def format_stream(self, text_stream):
        """
        Generator that formats text from a streaming source.
        
        Args:
            text_stream: An iterator/generator that yields text chunks
            
        Yields:
            Formatted text chunks ready for display
        """
        for chunk in text_stream:
            formatted = self.formatter.process_chunk(chunk)
            if formatted:
                yield formatted
        
        # Flush any remaining content
        final = self.formatter.flush()
        if final:
            yield final


def demo_streaming_formatter():
    """Demonstrate the streaming formatter with simulated LLM output."""
    import time
    import sys
    
    # Simulate LLM streaming output
    test_chunks = [
        "## Welcome to ",
        "the Stream",
        "ing Formatter",
        " Demo\n\n",
        "This demonstrates how **mark",
        "down** formatting works ",
        "with streaming text.\n\n",
        "Here's some `inline",
        " code` and here's ",
        "a list:\n\n",
        "- First item with **bold",
        "** text\n",
        "- Second item with *italic* text\n",
        "- Third item with `code`\n\n",
        "### Code Block Example\n\n",
        "```python\n",
        "def hello_world():\n",
        "    print('Hello, ",
        "World!')\n",
        "    return True\n",
        "```\n\n",
        "That's all folks!"
    ]
    
    formatter = StreamingFormatter()
    
    print("Streaming LLM output with real-time formatting:")
    print("=" * 50)
    
    for chunk in test_chunks:
        formatted = formatter.formatter.process_chunk(chunk)
        sys.stdout.write(formatted)
        sys.stdout.flush()
        time.sleep(0.1)  # Simulate streaming delay
    
    # Flush any remaining content
    final = formatter.formatter.flush()
    if final:
        sys.stdout.write(final)
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    demo_streaming_formatter()