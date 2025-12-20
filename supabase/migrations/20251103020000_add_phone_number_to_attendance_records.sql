alter table "public"."attendance_records"
  add column if not exists "phone_number" text;

alter table "public"."attendance_records"
  add constraint "chk_phone_number"
  check (phone_number is null or phone_number ~ '^\+[1-9][0-9]{1,14}$');
