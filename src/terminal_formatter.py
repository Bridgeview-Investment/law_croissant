"""
Terminal formatter for converting markdown syntax to colored terminal output.
Provides utilities to parse markdown and apply ANSI color codes for terminal display.
"""

import re
from typing import Dict, Tuple


class TerminalFormatter:
    """Converts markdown syntax to colored terminal output using ANSI escape codes."""
    
    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'UNDERLINE': '\033[4m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BRIGHT_RED': '\033[91m',
        'BRIGHT_GREEN': '\033[92m',
        'BRIGHT_YELLOW': '\033[93m',
        'BRIGHT_BLUE': '\033[94m',
        'BRIGHT_MAGENTA': '\033[95m',
        'BRIGHT_CYAN': '\033[96m',
        'BRIGHT_WHITE': '\033[97m',
        'BG_BLUE': '\033[44m',
        'BG_CYAN': '\033[46m',
        'BG_GRAY': '\033[100m',
    }
    
    def __init__(self, enable_colors: bool = True):
        """
        Initialize the terminal formatter.
        
        Args:
            enable_colors: Whether to enable color formatting (disable for non-terminal output)
        """
        self.enable_colors = enable_colors
    
    def format_text(self, text: str) -> str:
        """
        Convert markdown-formatted text to colored terminal output.
        
        Args:
            text: The markdown text to format
            
        Returns:
            Formatted text with ANSI color codes
        """
        if not self.enable_colors:
            return self._strip_markdown(text)
        
        # Process in order to avoid conflicts
        text = self._remove_emojis(text)
        text = self._format_code_blocks(text)
        text = self._format_inline_code(text)
        text = self._format_headers(text)
        text = self._format_bold(text)
        text = self._format_italic(text)
        text = self._format_underline(text)
        text = self._format_lists(text)
        text = self._format_tables(text)
        text = self._format_links(text)
        text = self._format_horizontal_rules(text)
        
        return text
    
    def _remove_emojis(self, text: str) -> str:
        """Remove all emoji characters from text."""
        # Remove common emojis used in the codebase
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251"  # Enclosed characters
            "]+", 
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)
    
    def _format_headers(self, text: str) -> str:
        """Format markdown headers with colors and formatting."""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.startswith('####'):
                # H4 - Cyan and bold
                content = line[4:].strip()
                formatted_lines.append(f"{self.COLORS['CYAN']}{self.COLORS['BOLD']}{content}{self.COLORS['RESET']}")
            elif line.startswith('###'):
                # H3 - Yellow and bold
                content = line[3:].strip()
                formatted_lines.append(f"{self.COLORS['YELLOW']}{self.COLORS['BOLD']}{content}{self.COLORS['RESET']}")
            elif line.startswith('##'):
                # H2 - Green and bold
                content = line[2:].strip()
                formatted_lines.append(f"{self.COLORS['GREEN']}{self.COLORS['BOLD']}{content}{self.COLORS['RESET']}")
            elif line.startswith('#'):
                # H1 - Blue and bold with underline
                content = line[1:].strip()
                formatted_lines.append(f"{self.COLORS['BLUE']}{self.COLORS['BOLD']}{self.COLORS['UNDERLINE']}{content}{self.COLORS['RESET']}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_bold(self, text: str) -> str:
        """Format bold text."""
        # Handle **text** pattern - use non-greedy match to handle nested cases better
        pattern = r'\*\*(.+?)\*\*'
        return re.sub(pattern, f"{self.COLORS['BOLD']}\\1{self.COLORS['RESET']}", text)
    
    def _format_italic(self, text: str) -> str:
        """Format italic text (displayed as dim in terminal)."""
        # Handle *text* pattern (single asterisk)
        pattern = r'(?<!\*)\*([^*]+)\*(?!\*)'
        return re.sub(pattern, f"{self.COLORS['DIM']}\\1{self.COLORS['RESET']}", text)
    
    def _format_underline(self, text: str) -> str:
        """Format underlined text."""
        # Handle __text__ pattern
        pattern = r'__([^_]+)__'
        return re.sub(pattern, f"{self.COLORS['UNDERLINE']}\\1{self.COLORS['RESET']}", text)
    
    def _format_inline_code(self, text: str) -> str:
        """Format inline code with background color."""
        # Handle `code` pattern
        pattern = r'`([^`]+)`'
        return re.sub(pattern, f"{self.COLORS['BG_GRAY']}{self.COLORS['WHITE']}\\1{self.COLORS['RESET']}", text)
    
    def _format_code_blocks(self, text: str) -> str:
        """Format code blocks with syntax highlighting simulation."""
        # Handle ```code``` blocks
        pattern = r'```(?:[a-zA-Z]+\n)?([^`]+)```'
        
        def replace_code_block(match):
            code = match.group(1)
            lines = code.split('\n')
            formatted_lines = []
            for line in lines:
                if line.strip():
                    formatted_lines.append(f"{self.COLORS['BG_GRAY']}{self.COLORS['BRIGHT_WHITE']}{line}{self.COLORS['RESET']}")
                else:
                    formatted_lines.append(line)
            return '\n'.join(formatted_lines)
        
        return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)
    
    def _format_lists(self, text: str) -> str:
        """Format list items with colored bullets."""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Unordered lists
            if re.match(r'^\s*[-*+]\s+', line):
                formatted_line = re.sub(
                    r'^(\s*)([-*+])(\s+)',
                    f"\\1{self.COLORS['CYAN']}\\2{self.COLORS['RESET']}\\3",
                    line
                )
                formatted_lines.append(formatted_line)
            # Ordered lists
            elif re.match(r'^\s*\d+\.\s+', line):
                formatted_line = re.sub(
                    r'^(\s*)(\d+\.)(\s+)',
                    f"\\1{self.COLORS['CYAN']}\\2{self.COLORS['RESET']}\\3",
                    line
                )
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_tables(self, text: str) -> str:
        """Format markdown tables with borders."""
        lines = text.split('\n')
        formatted_lines = []
        in_table = False
        
        for line in lines:
            if '|' in line:
                # Table row
                parts = line.split('|')
                formatted_parts = []
                for i, part in enumerate(parts):
                    if i == 0 or i == len(parts) - 1:
                        formatted_parts.append(f"{self.COLORS['DIM']}{part}{self.COLORS['RESET']}")
                    else:
                        formatted_parts.append(part)
                formatted_line = f"{self.COLORS['DIM']}|{self.COLORS['RESET']}".join(formatted_parts)
                formatted_lines.append(formatted_line)
                in_table = True
            else:
                formatted_lines.append(line)
                if in_table and line.strip() == '':
                    in_table = False
        
        return '\n'.join(formatted_lines)
    
    def _format_links(self, text: str) -> str:
        """Format markdown links."""
        # Handle [text](url) pattern
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        return re.sub(pattern, f"{self.COLORS['UNDERLINE']}{self.COLORS['BLUE']}\\1{self.COLORS['RESET']} ({self.COLORS['DIM']}\\2{self.COLORS['RESET']})", text)
    
    def _format_horizontal_rules(self, text: str) -> str:
        """Format horizontal rules."""
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if re.match(r'^[-*_]{3,}$', line.strip()):
                formatted_lines.append(f"{self.COLORS['DIM']}{'─' * 50}{self.COLORS['RESET']}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _strip_markdown(self, text: str) -> str:
        """Strip markdown syntax without adding colors."""
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove bold
        text = re.sub(r'\*\*([^*]+)\*\*', '\\1', text)
        # Remove italic
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', '\\1', text)
        # Remove underline
        text = re.sub(r'__([^_]+)__', '\\1', text)
        # Remove inline code
        text = re.sub(r'`([^`]+)`', '\\1', text)
        # Remove code blocks
        text = re.sub(r'```(?:[a-zA-Z]+\n)?([^`]+)```', '\\1', text, flags=re.DOTALL)
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', '\\1', text)
        # Remove emojis
        text = self._remove_emojis(text)
        
        return text


def format_for_terminal(text: str, enable_colors: bool = True) -> str:
    """
    Convenience function to format markdown text for terminal output.
    
    Args:
        text: The markdown text to format
        enable_colors: Whether to enable color formatting
        
    Returns:
        Formatted text suitable for terminal display
    """
    formatter = TerminalFormatter(enable_colors=enable_colors)
    return formatter.format_text(text)