create extension if not exists "supabase_vault";

create table if not exists public.attendance_credentials (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    company_id bigint not null,
    user_id_number bigint not null,
    vault_secret_id uuid not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uniq_attendance_credentials_user unique (user_id)
);

alter table public.attendance_credentials enable row level security;

create policy "Users can manage own attendance credentials"
    on public.attendance_credentials
    for all
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create or replace function public.create_attendance_secret(
    secret text,
    secret_name text default null,
    secret_description text default null
) returns uuid
language sql
security definer
set search_path = public, vault
as $$
    select vault.create_secret(secret, secret_name, secret_description);
$$;

create or replace function public.update_attendance_secret(
    secret_id uuid,
    secret text
) returns void
language sql
security definer
set search_path = public, vault
as $$
    select vault.update_secret(secret_id, secret, null, null);
$$;

create or replace function public.read_attendance_secret(
    secret_id uuid
) returns text
language sql
security definer
set search_path = public, vault
as $$
    select decrypted_secret
    from vault.decrypted_secrets
    where id = secret_id;
$$;

revoke all on function public.create_attendance_secret(text, text, text) from public;
revoke all on function public.update_attendance_secret(uuid, text) from public;
revoke all on function public.read_attendance_secret(uuid) from public;
grant execute on function public.create_attendance_secret(text, text, text) to service_role;
grant execute on function public.update_attendance_secret(uuid, text) to service_role;
grant execute on function public.read_attendance_secret(uuid) to service_role;
