-- Drop existing table and related objects
DROP TRIGGER IF EXISTS update_aws_profiles_updated_at ON aws_profiles;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP TABLE IF EXISTS aws_profiles CASCADE;

-- Create AWS Profiles table
CREATE TABLE aws_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    aws_access_key_id VARCHAR(100) NOT NULL,
    aws_secret_access_key VARCHAR(100) NOT NULL,
    aws_session_token TEXT,
    aws_region VARCHAR(50) NOT NULL DEFAULT 'us-east-1',
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add aws_session_token column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'aws_profiles'
        AND column_name = 'aws_session_token'
    ) THEN
        ALTER TABLE aws_profiles ADD COLUMN aws_session_token TEXT;
    END IF;
END $$;

-- Create function to update updated_at timestamp
CREATE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_aws_profiles_updated_at
    BEFORE UPDATE ON aws_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 