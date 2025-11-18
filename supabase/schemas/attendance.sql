-- Attendance scheduling storage for Supabase/Postgres.
-- Run with `supabase db push` or psql against your project's database.

-- Ensure the pgcrypto extension is available for gen_random_uuid().
create extension if not exists "pgcrypto";

-- Ensure the enum used for weekday arrays exists.
do
$$
begin
    if not exists (select 1 from pg_type where typname = 'weekday') then
        create type weekday as enum (
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday'
        );
    end if;
end
$$;

create table if not exists public.attendance_records (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    recorded_by uuid references auth.users (id),

    -- Status & configuration
    is_active boolean not null,
    timezone text not null,

    -- Entry schedule
    entry_enabled boolean not null,
    entry_local_time time not null,
    entry_utc_time time not null,
    entry_days weekday[] not null default '{}',

    -- Exit schedule
    exit_enabled boolean not null,
    exit_local_time time not null,
    exit_utc_time time not null,
    exit_days weekday[] not null default '{}',

    -- Location envelope
    location_address text not null,
    location_latitude numeric(9, 6) not null,
    location_longitude numeric(9, 6) not null,
    location_radius_meters numeric(10, 2) not null,

    recorded_at timestamptz not null default now(),

    constraint uniq_attendance_records_user unique (user_id),
    -- Constraints to keep data consistent with the API contract.
    constraint chk_entry_days
        check (entry_enabled = false or coalesce(array_length(entry_days, 1), 0) > 0),
    constraint chk_exit_days
        check (exit_enabled = false or coalesce(array_length(exit_days, 1), 0) > 0),
    constraint chk_latitude
        check (location_latitude between -90 and 90),
    constraint chk_longitude
        check (location_longitude between -180 and 180),
    constraint chk_radius
        check (location_radius_meters > 0)
);

create index if not exists attendance_records_user_idx
    on public.attendance_records (user_id, recorded_at desc);

create index if not exists attendance_records_active_idx
    on public.attendance_records (is_active)
    where is_active = true;

create index if not exists attendance_records_entry_days_idx
    on public.attendance_records using gin (entry_days);

create index if not exists attendance_records_exit_days_idx
    on public.attendance_records using gin (exit_days);
