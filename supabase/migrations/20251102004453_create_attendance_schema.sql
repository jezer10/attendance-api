create type "public"."weekday" as enum ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday');


  create table "public"."attendance_records" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "recorded_by" uuid,
    "is_active" boolean not null,
    "timezone" text not null,
    "entry_enabled" boolean not null,
    "entry_local_time" time without time zone not null,
    "entry_utc_time" time without time zone not null,
    "entry_days" public.weekday[] not null default '{}'::public.weekday[],
    "exit_enabled" boolean not null,
    "exit_local_time" time without time zone not null,
    "exit_utc_time" time without time zone not null,
    "exit_days" public.weekday[] not null default '{}'::public.weekday[],
    "location_address" text not null,
    "location_latitude" numeric(9,6) not null,
    "location_longitude" numeric(9,6) not null,
    "location_radius_meters" numeric(10,2) not null,
    "recorded_at" timestamp with time zone not null default now()
      );


CREATE INDEX attendance_records_active_idx ON public.attendance_records USING btree (is_active) WHERE (is_active = true);

CREATE INDEX attendance_records_entry_days_idx ON public.attendance_records USING gin (entry_days);

CREATE INDEX attendance_records_exit_days_idx ON public.attendance_records USING gin (exit_days);

CREATE UNIQUE INDEX attendance_records_pkey ON public.attendance_records USING btree (id);

CREATE INDEX attendance_records_user_idx ON public.attendance_records USING btree (user_id, recorded_at DESC);

alter table "public"."attendance_records" add constraint "attendance_records_pkey" PRIMARY KEY using index "attendance_records_pkey";

alter table "public"."attendance_records" add constraint "attendance_records_recorded_by_fkey" FOREIGN KEY (recorded_by) REFERENCES auth.users(id) not valid;

alter table "public"."attendance_records" validate constraint "attendance_records_recorded_by_fkey";

alter table "public"."attendance_records" add constraint "attendance_records_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."attendance_records" validate constraint "attendance_records_user_id_fkey";

alter table "public"."attendance_records" add constraint "chk_entry_days" CHECK (((entry_enabled = false) OR (COALESCE(array_length(entry_days, 1), 0) > 0))) not valid;

alter table "public"."attendance_records" validate constraint "chk_entry_days";

alter table "public"."attendance_records" add constraint "chk_exit_days" CHECK (((exit_enabled = false) OR (COALESCE(array_length(exit_days, 1), 0) > 0))) not valid;

alter table "public"."attendance_records" validate constraint "chk_exit_days";

alter table "public"."attendance_records" add constraint "chk_latitude" CHECK (((location_latitude >= ('-90'::integer)::numeric) AND (location_latitude <= (90)::numeric))) not valid;

alter table "public"."attendance_records" validate constraint "chk_latitude";

alter table "public"."attendance_records" add constraint "chk_longitude" CHECK (((location_longitude >= ('-180'::integer)::numeric) AND (location_longitude <= (180)::numeric))) not valid;

alter table "public"."attendance_records" validate constraint "chk_longitude";

alter table "public"."attendance_records" add constraint "chk_radius" CHECK ((location_radius_meters > (0)::numeric)) not valid;

alter table "public"."attendance_records" validate constraint "chk_radius";

grant delete on table "public"."attendance_records" to "anon";

grant insert on table "public"."attendance_records" to "anon";

grant references on table "public"."attendance_records" to "anon";

grant select on table "public"."attendance_records" to "anon";

grant trigger on table "public"."attendance_records" to "anon";

grant truncate on table "public"."attendance_records" to "anon";

grant update on table "public"."attendance_records" to "anon";

grant delete on table "public"."attendance_records" to "authenticated";

grant insert on table "public"."attendance_records" to "authenticated";

grant references on table "public"."attendance_records" to "authenticated";

grant select on table "public"."attendance_records" to "authenticated";

grant trigger on table "public"."attendance_records" to "authenticated";

grant truncate on table "public"."attendance_records" to "authenticated";

grant update on table "public"."attendance_records" to "authenticated";

grant delete on table "public"."attendance_records" to "service_role";

grant insert on table "public"."attendance_records" to "service_role";

grant references on table "public"."attendance_records" to "service_role";

grant select on table "public"."attendance_records" to "service_role";

grant trigger on table "public"."attendance_records" to "service_role";

grant truncate on table "public"."attendance_records" to "service_role";

grant update on table "public"."attendance_records" to "service_role";


