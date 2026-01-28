-- Paper Scraper Database Initialization
-- This script runs automatically when the PostgreSQL container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions (useful for development)
GRANT ALL PRIVILEGES ON DATABASE paperscraper TO postgres;
