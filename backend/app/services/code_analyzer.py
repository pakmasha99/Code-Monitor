"""
Code Analysis Service using LLM and tree-sitter

Provides code parsing, chunking, and LLM-based analysis capabilities.
"""
from anthropic import Anthropic
import openai
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class CodeAnalyzer:
    """
    Analyzes code using tree-sitter for parsing and Claude/GPT for insights.

    Supports Python and JavaScript with extensible parser architecture.
    """

    def __init__(self):
        """Initialize LLM clients and code parsers"""
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        openai.api_key = os.getenv("OPENAI_API_KEY")
        # Use latest Claude 4.5 Sonnet (Sept 2025) - best for coding & agents
        self.llm_model = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")
        self.setup_parsers()

    def setup_parsers(self):
        """Setup tree-sitter parsers for different languages"""
        self.parsers = {}

        # Python parser
        python_lang = Language(tspython.language())
        self.parsers['python'] = Parser(python_lang)

        # JavaScript parser
        js_lang = Language(tsjavascript.language())
        self.parsers['javascript'] = Parser(js_lang)
        self.parsers['typescript'] = self.parsers['javascript']  # Share JS parser for TS

    def detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension

        Args:
            file_path: Path to source file

        Returns:
            Language identifier (python, javascript, etc.) or 'unknown'
        """
        ext = Path(file_path).suffix.lower().lstrip('.')

        mapping = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rs': 'rust'
        }

        return mapping.get(ext, 'unknown')

    def extract_name(self, node, source_bytes: bytes) -> str:
        """
        Extract function/class name from AST node

        Args:
            node: Tree-sitter node
            source_bytes: Original source code as bytes

        Returns:
            Extracted name or 'unknown'
        """
        # Look for identifier child node
        for child in node.children:
            if child.type == 'identifier':
                return source_bytes[child.start_byte:child.end_byte].decode('utf8')

        return 'unknown'

    def chunk_code_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Parse code into logical chunks using tree-sitter

        Args:
            file_path: Path to the source file
            content: File content as string

        Returns:
            List of code chunks with metadata
        """
        language = self.detect_language(file_path)
        parser = self.parsers.get(language)

        if not parser:
            # Fallback for unsupported languages
            return self.simple_chunk(content, language)

        source_bytes = bytes(content, 'utf8')
        tree = parser.parse(source_bytes)
        chunks = []

        # Define node types to extract based on language
        target_types = {
            'python': ['function_definition', 'class_definition'],
            'javascript': ['function_declaration', 'class_declaration',
                          'function_expression', 'arrow_function'],
            'typescript': ['function_declaration', 'class_declaration',
                          'function_expression', 'arrow_function']
        }

        types_to_extract = target_types.get(language, [])

        def traverse(node):
            """Recursively traverse AST to find target nodes"""
            if node.type in types_to_extract:
                chunk = {
                    'type': node.type,
                    'name': self.extract_name(node, source_bytes),
                    'code': content[node.start_byte:node.end_byte],
                    'start_line': node.start_point[0] + 1,  # 1-indexed
                    'end_line': node.end_point[0] + 1,
                    'language': language,
                    'file_path': file_path
                }
                chunks.append(chunk)

            # Continue traversing for nested structures
            for child in node.children:
                traverse(child)

        traverse(tree.root_node)

        return chunks if chunks else self.simple_chunk(content, language)

    def simple_chunk(self, content: str, language: str = 'unknown') -> List[Dict[str, Any]]:
        """
        Fallback simple chunking for unsupported languages

        Splits code by function/class definitions using regex patterns.

        Args:
            content: Source code content
            language: Language identifier

        Returns:
            List of simple chunks
        """
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        start_line = 0

        for i, line in enumerate(lines):
            # Check for function/class definitions
            if line.strip().startswith(('def ', 'class ', 'function ', 'async def ',
                                       'export function', 'export class')):
                # Save previous chunk if exists
                if current_chunk:
                    chunks.append({
                        'code': '\n'.join(current_chunk),
                        'type': 'code_block',
                        'language': language,
                        'start_line': start_line + 1,
                        'end_line': i,
                        'name': 'unknown'
                    })

                # Start new chunk
                current_chunk = [line]
                start_line = i
            else:
                current_chunk.append(line)

        # Add final chunk
        if current_chunk:
            chunks.append({
                'code': '\n'.join(current_chunk),
                'type': 'code_block',
                'language': language,
                'start_line': start_line + 1,
                'end_line': len(lines),
                'name': 'unknown'
            })

        return chunks

    async def analyze_code_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code chunk with Claude 3.5 Sonnet

        Args:
            chunk: Code chunk dictionary with code, language, type

        Returns:
            Analysis results with summary, complexity, quality metrics
        """
        prompt = f"""Analyze this {chunk['language']} {chunk['type']} code:

```{chunk['language']}
{chunk['code']}
```

Provide a JSON response with:
1. "summary": One-sentence description of what this code does
2. "purpose": Detailed explanation of its purpose
3. "complexity": Complexity score from 1-10 (1=trivial, 10=very complex)
4. "algorithms": List of key algorithms or patterns used
5. "quality": Code quality assessment (readability, maintainability, best practices)

Format as valid JSON only, no markdown."""

        try:
            message = self.anthropic.messages.create(
                model=self.llm_model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse JSON response
            analysis = json.loads(message.content[0].text)
            return analysis

        except json.JSONDecodeError as e:
            # Fallback if LLM doesn't return valid JSON
            return {
                "summary": "Analysis failed - invalid JSON response",
                "purpose": str(e),
                "complexity": 5,
                "algorithms": [],
                "quality": "Could not analyze"
            }
        except Exception as e:
            # Generic error handling
            return {
                "summary": f"Analysis failed: {str(e)}",
                "purpose": "Error during analysis",
                "complexity": 0,
                "algorithms": [],
                "quality": "Error"
            }

    async def analyze_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Analyze entire file by chunking and analyzing each chunk

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of analyzed chunks with metadata and LLM insights
        """
        chunks = self.chunk_code_file(file_path, content)
        analyzed_chunks = []

        for chunk in chunks:
            analysis = await self.analyze_code_chunk(chunk)
            analyzed_chunks.append({
                **chunk,
                'analysis': analysis
            })

        return analyzed_chunks
