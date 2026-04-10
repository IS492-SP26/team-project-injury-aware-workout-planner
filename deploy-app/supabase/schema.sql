create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  full_name text,
  age integer check (age is null or age between 10 and 120),
  gender text,
  height_unit text check (height_unit is null or height_unit in ('cm', 'ft_in')),
  height_value numeric,
  onboarding_completed boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.injury_assessments (
  user_id uuid primary key references public.users(id) on delete cascade,
  body_part text,
  diagnosis text,
  date_of_injury date,
  training_experience text,
  activity_level text,
  goals jsonb not null default '[]'::jsonb,
  pain_daily integer check (pain_daily is null or pain_daily between 0 and 10),
  pain_squat integer check (pain_squat is null or pain_squat between 0 and 10),
  pain_stairs integer check (pain_stairs is null or pain_stairs between 0 and 10),
  functional_screening jsonb not null default '[]'::jsonb,
  movement_limitations jsonb not null default '[]'::jsonb,
  raw_payload jsonb not null default '{}'::jsonb,
  backend_session_id text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.youtube_videos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  source text not null check (source in ('youtube', 'text')),
  youtube_url text,
  youtube_video_id text,
  video_title text,
  workout_text text,
  backend_session_id text,
  video_timestamps jsonb not null default '[]'::jsonb,
  analysis_rows jsonb not null default '[]'::jsonb,
  markdown_table text,
  backend_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists youtube_videos_user_created_idx
  on public.youtube_videos (user_id, created_at desc);

create index if not exists youtube_videos_user_video_id_idx
  on public.youtube_videos (user_id, youtube_video_id)
  where youtube_video_id is not null;

create trigger set_users_updated_at
before update on public.users
for each row
execute function public.set_updated_at();

create trigger set_injury_assessments_updated_at
before update on public.injury_assessments
for each row
execute function public.set_updated_at();

create trigger set_youtube_videos_updated_at
before update on public.youtube_videos
for each row
execute function public.set_updated_at();

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.users (id, email)
  values (new.id, coalesce(new.email, ''))
  on conflict (id) do update
    set email = excluded.email,
        updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_auth_user();

alter table public.users enable row level security;
alter table public.injury_assessments enable row level security;
alter table public.youtube_videos enable row level security;

drop policy if exists "users_select_own" on public.users;
create policy "users_select_own"
on public.users
for select
using (auth.uid() is not null and auth.uid() = id);

drop policy if exists "users_update_own" on public.users;
create policy "users_update_own"
on public.users
for update
using (auth.uid() is not null and auth.uid() = id);

drop policy if exists "users_insert_own" on public.users;
create policy "users_insert_own"
on public.users
for insert
with check (auth.uid() is not null and auth.uid() = id);

drop policy if exists "injury_assessments_own_all" on public.injury_assessments;
create policy "injury_assessments_own_all"
on public.injury_assessments
for all
using (auth.uid() is not null and auth.uid() = user_id)
with check (auth.uid() is not null and auth.uid() = user_id);

drop policy if exists "youtube_videos_own_all" on public.youtube_videos;
create policy "youtube_videos_own_all"
on public.youtube_videos
for all
using (auth.uid() is not null and auth.uid() = user_id)
with check (auth.uid() is not null and auth.uid() = user_id);
