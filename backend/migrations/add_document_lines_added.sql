-- Migration: Add document_lines_added column to weekly_submissions table
-- Date: 2024-10-22
-- Description: Track actual line count from documents (PDFs, text files, etc.)

-- Add the column with default value 0
ALTER TABLE weekly_submissions
ADD COLUMN document_lines_added INTEGER NOT NULL DEFAULT 0;

-- Optional: Update existing records to migrate from documents_created
-- This converts documents_created count to estimated lines (100 lines per doc)
-- UPDATE weekly_submissions
-- SET document_lines_added = documents_created * 100
-- WHERE document_lines_added = 0 AND documents_created > 0;
