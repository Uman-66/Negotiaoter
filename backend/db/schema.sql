-- The live Uman Supabase schema: flat columns, text IDs.
create table if not exists public.specs (
  id text primary key, property_type text not null, property_sqft integer not null,
  property_bedrooms integer not null, property_bathrooms numeric not null, property_levels integer not null default 1,
  clean_type text not null, frequency text not null, clutter_level text not null, has_pets boolean not null default false,
  weeks_since_last_clean integer not null default 0, add_on_fridge boolean not null default false,
  add_on_oven boolean not null default false, add_on_windows boolean not null default false,
  add_on_baseboards boolean not null default false, add_on_laundry boolean not null default false,
  access_parking text not null, access_entry_method text not null, access_walk_up_floor integer not null default 0,
  schedule_preferred_date text not null, schedule_preferred_time_window text not null, schedule_flexibility text,
  open_questions jsonb not null default '[]'::jsonb, confirmed_by_user boolean not null default false,
  intake_source text not null, created_at timestamptz not null default now()
);
create table if not exists public.companies (id text primary key, name text not null unique, persona text not null, created_at timestamptz not null default now());
create table if not exists public.calls (id text primary key, spec_id text not null references public.specs(id) on delete cascade, company_id text not null references public.companies(id), status text not null default 'queued', created_at timestamptz not null default now(), updated_at timestamptz not null default now(), unique(spec_id, company_id));
create table if not exists public.quotes (id text primary key, call_id text not null references public.calls(id) on delete cascade, company_id text not null references public.companies(id), spec_id text not null references public.specs(id), outcome text not null, pricing_model text, opening_total numeric, final_total numeric, total numeric, moved_because text, conditions jsonb not null default '[]'::jsonb, red_flags jsonb not null default '[]'::jsonb, red_flag_reasons jsonb not null default '[]'::jsonb, callback_contact text, callback_window text, notes text, transcript_url text, recording_url text, created_at timestamptz not null default now());
create table if not exists public.quote_items (id bigint generated always as identity primary key, quote_id text not null references public.quotes(id) on delete cascade, call_id text, label text not null, amount numeric not null, disclosed_voluntarily boolean not null default true, negotiable boolean not null default false, created_at timestamptz not null default now());
