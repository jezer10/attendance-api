-- Add random window configuration to attendance records
alter table "public"."attendance_records"
  add column if not exists "random_window_minutes" integer not null default 0;

-- Ensure event type enum exists
DO $$
begin
  if not exists (select 1 from pg_type where typname = 'attendance_event_type') then
    create type attendance_event_type as enum ('entry', 'exit');
  end if;
end
$$;

-- Attendance events history
create table if not exists "public"."attendance_events" (
  "id" uuid not null default gen_random_uuid(),
  "user_id" uuid not null references auth.users (id) on delete cascade,
  "event_type" attendance_event_type not null,
  "event_date" date not null,
  "scheduled_for" timestamptz not null,
  "marked_at" timestamptz not null default now(),
  "timezone" text not null,
  "base_local_time" time not null,
  "random_window_minutes" integer not null,
  "offset_minutes" integer not null,
  "created_at" timestamptz not null default now(),
  constraint "attendance_events_pkey" primary key ("id"),
  constraint "uniq_attendance_event" unique ("user_id", "event_date", "event_type"),
  constraint "chk_random_window_minutes" check (random_window_minutes >= 0)
);

create index if not exists "attendance_events_user_idx"
  on "public"."attendance_events" ("user_id", "event_date" desc);
