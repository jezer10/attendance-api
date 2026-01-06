alter table "public"."attendance_events"
  add column if not exists "notified_at" timestamptz;

create index if not exists "attendance_events_notified_idx"
  on "public"."attendance_events" ("notified_at");
