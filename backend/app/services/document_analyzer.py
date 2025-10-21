"""
Document analyzer service for counting lines in various document formats
"""
import os
from typing import Optional
import PyPDF2
from pathlib import Path


class DocumentAnalyzer:
    """Service for analyzing documents and counting lines"""

    @staticmethod
    def count_lines_in_file(file_path: str) -> int:
        """
        Count lines in a file (supports text files and PDFs)

        Args:
            file_path: Path to the file

        Returns:
            Number of lines in the file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_extension = Path(file_path).suffix.lower()

        if file_extension == '.pdf':
            return DocumentAnalyzer._count_pdf_lines(file_path)
        elif file_extension in ['.txt', '.md', '.rst', '.tex']:
            return DocumentAnalyzer._count_text_lines(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    @staticmethod
    def _count_text_lines(file_path: str) -> int:
        """
        Count lines in a text file

        Args:
            file_path: Path to text file

        Returns:
            Number of non-empty lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f.readlines()]
                # Count non-empty lines
                return sum(1 for line in lines if line)
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return 0

    @staticmethod
    def _count_pdf_lines(file_path: str) -> int:
        """
        Count lines in a PDF file

        Estimates line count based on text content extraction.
        Each extracted text chunk is split by newlines to estimate lines.

        Args:
            file_path: Path to PDF file

        Returns:
            Estimated number of lines
        """
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_lines = 0

                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        # Split by newlines and count non-empty lines
                        lines = [line.strip() for line in text.split('\n')]
                        total_lines += sum(1 for line in lines if line)

                return total_lines

        except Exception as e:
            print(f"Error reading PDF file {file_path}: {e}")
            return 0

    @staticmethod
    def count_lines_in_directory(
        directory_path: str,
        extensions: Optional[list] = None
    ) -> dict:
        """
        Count lines in all supported documents in a directory

        Args:
            directory_path: Path to directory
            extensions: List of file extensions to include (e.g., ['.pdf', '.txt'])
                       If None, includes all supported formats

        Returns:
            Dict with total_lines and breakdown by file type
        """
        if extensions is None:
            extensions = ['.pdf', '.txt', '.md', '.rst', '.tex']

        results = {
            'total_lines': 0,
            'files_processed': 0,
            'breakdown': {},
            'errors': []
        }

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()

                if file_ext in extensions:
                    try:
                        line_count = DocumentAnalyzer.count_lines_in_file(file_path)
                        results['total_lines'] += line_count
                        results['files_processed'] += 1

                        # Track breakdown by extension
                        if file_ext not in results['breakdown']:
                            results['breakdown'][file_ext] = 0
                        results['breakdown'][file_ext] += line_count

                    except Exception as e:
                        results['errors'].append({
                            'file': file_path,
                            'error': str(e)
                        })

        return results
