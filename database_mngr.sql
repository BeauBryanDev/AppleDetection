-- Add missing columns to database tables

-- Add address and is_active to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1;

-- Add address to orchards table
ALTER TABLE orchards ADD COLUMN IF NOT EXISTS address VARCHAR;

-- Add user_notes to predictions table
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS user_notes VARCHAR(500);

-- Show confirmation
SELECT 'Column additions complete!' as status;
