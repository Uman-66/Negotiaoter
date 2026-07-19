-- The Negotiator — Supabase Schema Setup (Cleaning Vertical)
-- Copy and paste this into the Supabase SQL Editor (Dashboard -> SQL Editor -> New Query)

-- 1. Create specs table
CREATE TABLE IF NOT EXISTS specs (
    id TEXT PRIMARY KEY,
    property_type TEXT NOT NULL,
    property_sqft INTEGER NOT NULL,
    property_bedrooms INTEGER NOT NULL,
    property_bathrooms DOUBLE PRECISION NOT NULL,
    property_levels INTEGER DEFAULT 1,
    clean_type TEXT NOT NULL,
    frequency TEXT NOT NULL,
    clutter_level TEXT NOT NULL,
    has_pets BOOLEAN NOT NULL,
    weeks_since_last_clean INTEGER NOT NULL,
    add_on_fridge BOOLEAN DEFAULT FALSE,
    add_on_oven BOOLEAN DEFAULT FALSE,
    add_on_windows BOOLEAN DEFAULT FALSE,
    add_on_baseboards BOOLEAN DEFAULT FALSE,
    add_on_laundry BOOLEAN DEFAULT FALSE,
    access_parking TEXT NOT NULL,
    access_entry_method TEXT NOT NULL,
    access_walk_up_floor INTEGER DEFAULT 0,
    schedule_preferred_date TEXT NOT NULL,
    schedule_preferred_time_window TEXT NOT NULL,
    schedule_flexibility TEXT,
    open_questions JSONB DEFAULT '[]'::jsonb,
    confirmed_by_user BOOLEAN DEFAULT FALSE,
    intake_source TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    persona TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. Create calls table
CREATE TABLE IF NOT EXISTS calls (
    id TEXT PRIMARY KEY,
    spec_id TEXT NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'queued',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 4. Create quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id TEXT PRIMARY KEY,
    call_id TEXT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    spec_id TEXT NOT NULL REFERENCES specs(id) ON DELETE CASCADE,
    outcome TEXT NOT NULL,
    pricing_model TEXT,
    opening_total DOUBLE PRECISION,
    final_total DOUBLE PRECISION,
    total DOUBLE PRECISION,
    moved_because TEXT,
    conditions JSONB DEFAULT '[]'::jsonb,
    red_flags JSONB DEFAULT '[]'::jsonb,
    red_flag_reasons JSONB DEFAULT '[]'::jsonb,
    callback_contact TEXT,
    callback_window TEXT,
    notes TEXT,
    transcript_url TEXT,
    recording_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 5. Create quote_items table
CREATE TABLE IF NOT EXISTS quote_items (
    id SERIAL PRIMARY KEY,
    quote_id TEXT NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    call_id TEXT,
    label TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    disclosed_voluntarily BOOLEAN DEFAULT TRUE,
    negotiable BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Seed mock companies
INSERT INTO companies (id, name, persona) VALUES
('company_1', 'Apex Cleaning Co', 'Premium'),
('company_2', 'Budget Cleaners', 'Lowballer'),
('company_3', 'Sparkle & Shine', 'Upseller')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, persona = EXCLUDED.persona;

-- Disable Row Level Security (RLS) or enable public read/write so the frontend & webhooks can interact directly.
-- (Supabase default is to require RLS policies unless disabled)
ALTER TABLE specs DISABLE ROW LEVEL SECURITY;
ALTER TABLE companies DISABLE ROW LEVEL SECURITY;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE quotes DISABLE ROW LEVEL SECURITY;
ALTER TABLE quote_items DISABLE ROW LEVEL SECURITY;
