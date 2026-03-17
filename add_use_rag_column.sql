-- SQL script to add use_rag column to assignment_assignment table
-- Run this in your SQLite database if migrations don't work

ALTER TABLE assignment_assignment ADD COLUMN use_rag INTEGER DEFAULT 1 NOT NULL;

-- Verify the column was added
-- SELECT * FROM assignment_assignment LIMIT 1;
