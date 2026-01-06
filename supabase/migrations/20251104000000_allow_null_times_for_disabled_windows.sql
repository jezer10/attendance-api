alter table "public"."attendance_records"
  alter column "entry_local_time" drop not null,
  alter column "entry_utc_time" drop not null,
  alter column "exit_local_time" drop not null,
  alter column "exit_utc_time" drop not null;

alter table "public"."attendance_records"
  add constraint "chk_entry_times"
  check (
    "entry_enabled" = false
    or ("entry_local_time" is not null and "entry_utc_time" is not null)
  );

alter table "public"."attendance_records"
  add constraint "chk_exit_times"
  check (
    "exit_enabled" = false
    or ("exit_local_time" is not null and "exit_utc_time" is not null)
  );
