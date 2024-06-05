import re
import os
import tempfile
import subprocess
import unittest

from dataclasses import dataclass
from typing import Iterator, Union, Callable
from typing_extensions import TypeGuard

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from pygments.util import ClassNotFound


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class SyntaxError(Error):
    """Denotes error in parsing markdown"""

    pass


class SyntaxHighlightingError(Error):
    """Denotes error in highlighting a code block"""

    pass


@dataclass
class CodeBlock:
    language: str
    code: str

    def to_highlighted_string(self) -> str:
        try:
            lexer = get_lexer_by_name(self.language)
            return highlight(self.code, lexer, TerminalFormatter())
        except ClassNotFound as e:
            raise SyntaxHighlightingError("Syntax highlighting error: " + str(e))


class MarkdownLine:
    def __init__(self, line: str):
        self.line = line

    def raw(self) -> str:
        return self.line

    def is_code_fence(self) -> bool:
        return self.stripped_line().startswith("```")

    def code_fence_language(self) -> str:
        if not self.is_code_fence():
            raise Error("Line is not a code fence")

        return self.stripped_line()[3:].strip()

    def stripped_line(self) -> str:
        """Returns the line with proceeding whitespace removed"""
        return self.line[self.indent_level() :]

    def indent_level(self) -> int:
        """Returns the number of whitespace characters at the beginning of the line"""
        num_whitespace = 0
        for char in self.line:
            if char in [" ", "\t"]:
                num_whitespace += 1
            else:
                break

        return num_whitespace


class MarkdownDocument:
    def __init__(self, markdown: str):
        self.markdown = markdown

    def to_highlighted_string(self) -> str:
        out = ""
        for node in self.get_nodes():
            if isinstance(node, CodeBlock):
                out += node.to_highlighted_string() + "\n"
            else:
                out += node.raw() + "\n"

        return out

    def get_code_blocks(self) -> list[CodeBlock]:
        is_code_block: Callable[
            [Union[MarkdownLine, CodeBlock]], TypeGuard[CodeBlock]
        ] = lambda node: isinstance(node, CodeBlock)

        return list(filter(is_code_block, self.get_nodes()))

    def get_nodes(self) -> list[Union[MarkdownLine, CodeBlock]]:
        within_code_block = False
        nodes: list[Union[MarkdownLine, CodeBlock]] = []

        def extract_code(
            lines_iter: Iterator[MarkdownLine], fence_indent_level: int
        ) -> str:
            """Consumes the iterator until the end of the code block and returns the code"""

            code = ""
            for line in lines_iter:
                if line.indent_level() < fence_indent_level:
                    raise SyntaxError(
                        "Code block indentation level does not match fence"
                    )
                elif line.is_code_fence():
                    return code
                else:
                    code += line.raw()[fence_indent_level:] + "\n"

            raise SyntaxError("Code block not terminated")

        lines_iter = map(lambda l: MarkdownLine(l), iter(self.markdown.splitlines()))

        for line in lines_iter:
            if line.is_code_fence():
                # extract_code consumes the iter, so the for loop will advance to the
                # end of the code block
                block = CodeBlock(
                    line.code_fence_language(),
                    extract_code(lines_iter, line.indent_level()),
                )
                nodes.append(block)
            else:
                nodes.append(line)

        return nodes


def extract_code_blocks(markdown: str) -> list[CodeBlock]:
    """Extracts code blocks from markdown text"""
    return MarkdownDocument(markdown).get_code_blocks()


# Allow testing by running this file directly
if __name__ == "__main__":

    class TestMarkDownProcessor(unittest.TestCase):
        def test_extract_code_blocks(self):
            # Test case 1: Markdown with multiple code blocks
            markdown = """
            Some text here

            ```python
              print("Hello, world!")
            ```

            Some more text

            ```bash
            echo "This is a code block in Bash"
            ```
            """
            blocks = extract_code_blocks(markdown)

            self.assertEqual(len(blocks), 2)

            def assert_block(block, language, code):
                self.assertIsInstance(block, CodeBlock)
                self.assertEqual(block.language, language)
                self.assertEqual(block.code, code)

            assert_block(blocks[0], "python", '  print("Hello, world!")\n')
            assert_block(blocks[1], "bash", 'echo "This is a code block in Bash"\n')

            # Test case 2: Markdown with no code blocks
            markdown = "This is a regular text"
            blocks = extract_code_blocks(markdown)

            self.assertEqual(len(blocks), 0)

    unittest.main()
