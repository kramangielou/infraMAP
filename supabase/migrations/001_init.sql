create extension if not exists postgis;
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role text not null default 'VIEWER' check (role in ('ADMIN','VIEWER')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  project_code text not null unique,
  project_name text not null,
  description text,
  project_type text not null,
  sector text not null,
  status text not null default 'PENDING' check (status in ('PENDING','ONGOING','COMPLETED','DELAYED','SUSPENDED')),
  completion_percentage numeric(5,2) not null default 0 check (completion_percentage between 0 and 100),
  budget numeric(18,2) not null default 0 check (budget >= 0),
  contract_amount numeric(18,2) check (contract_amount is null or contract_amount >= 0),
  funding_source text,
  contractor text,
  contract_reference text,
  implementing_agency text,
  location_name text,
  barangay text,
  city text,
  province text,
  start_date date,
  target_end_date date,
  actual_completion_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  created_by uuid references public.profiles(id),
  updated_by uuid references public.profiles(id),
  archived_at timestamptz,
  geometry geometry(Geometry,4326),
  constraint project_dates_check check (target_end_date is null or start_date is null or target_end_date >= start_date),
  constraint project_actual_date_check check (actual_completion_date is null or start_date is null or actual_completion_date >= start_date),
  constraint project_geometry_check check (geometry is null or GeometryType(geometry) in ('POINT','LINESTRING','POLYGON'))
);

create table if not exists public.project_progress (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  progress_percentage numeric(5,2) not null check (progress_percentage between 0 and 100),
  progress_date date not null,
  remarks text,
  recorded_by uuid references public.profiles(id),
  created_at timestamptz not null default now(),
  unique(project_id,id)
);

create table if not exists public.project_progress_media (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  progress_id uuid not null references public.project_progress(id) on delete cascade,
  file_name text not null,
  file_path text not null unique,
  file_type text not null check (file_type in ('image/jpeg','image/png','image/webp')),
  file_size bigint not null check (file_size > 0),
  caption text,
  taken_at timestamptz,
  uploaded_by uuid references public.profiles(id),
  created_at timestamptz not null default now(),
  constraint media_progress_project_fk foreign key(project_id,progress_id) references public.project_progress(project_id,id) on delete cascade
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id),
  entity_type text not null,
  entity_id uuid,
  action text not null,
  old_data jsonb,
  new_data jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_projects_code on public.projects(project_code);
create index if not exists idx_projects_status on public.projects(status);
create index if not exists idx_projects_start_date on public.projects(start_date);
create index if not exists idx_projects_target_end on public.projects(target_end_date);
create index if not exists idx_projects_type on public.projects(project_type);
create index if not exists idx_projects_city on public.projects(city);
create index if not exists idx_projects_province on public.projects(province);
create index if not exists idx_projects_contractor on public.projects(contractor);
create index if not exists idx_projects_geometry_gist on public.projects using gist(geometry);
create index if not exists idx_progress_project_date on public.project_progress(project_id,progress_date desc);
create index if not exists idx_media_progress on public.project_progress_media(progress_id);

create or replace function public.is_admin() returns boolean language sql stable security definer set search_path=public as $$
  select exists(select 1 from public.profiles where id=auth.uid() and role='ADMIN');
$$;

create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path=public as $$
begin insert into public.profiles(id,full_name,role) values(new.id,coalesce(new.raw_user_meta_data->>'full_name',''), 'VIEWER') on conflict (id) do nothing; return new; end; $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute function public.handle_new_user();

alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.project_progress enable row level security;
alter table public.project_progress_media enable row level security;
alter table public.audit_logs enable row level security;

drop policy if exists profiles_select on public.profiles;
create policy profiles_select on public.profiles for select to authenticated using (id=auth.uid() or public.is_admin());
drop policy if exists projects_select on public.projects;
create policy projects_select on public.projects for select to authenticated using (archived_at is null);
drop policy if exists projects_admin_insert on public.projects;
create policy projects_admin_insert on public.projects for insert to authenticated with check (public.is_admin());
drop policy if exists projects_admin_update on public.projects;
create policy projects_admin_update on public.projects for update to authenticated using (public.is_admin()) with check (public.is_admin());
drop policy if exists projects_admin_delete on public.projects;
create policy projects_admin_delete on public.projects for delete to authenticated using (public.is_admin());

drop policy if exists progress_select on public.project_progress;
create policy progress_select on public.project_progress for select to authenticated using (exists(select 1 from public.projects p where p.id=project_id and p.archived_at is null));
drop policy if exists progress_admin_insert on public.project_progress;
create policy progress_admin_insert on public.project_progress for insert to authenticated with check (public.is_admin());
drop policy if exists progress_admin_update on public.project_progress;
create policy progress_admin_update on public.project_progress for update to authenticated using (public.is_admin()) with check (public.is_admin());
drop policy if exists progress_admin_delete on public.project_progress;
create policy progress_admin_delete on public.project_progress for delete to authenticated using (public.is_admin());

drop policy if exists media_select on public.project_progress_media;
create policy media_select on public.project_progress_media for select to authenticated using (exists(select 1 from public.project_progress pp join public.projects p on p.id=pp.project_id where pp.id=progress_id and p.archived_at is null));
drop policy if exists media_admin_insert on public.project_progress_media;
create policy media_admin_insert on public.project_progress_media for insert to authenticated with check (public.is_admin());
drop policy if exists media_admin_delete on public.project_progress_media;
create policy media_admin_delete on public.project_progress_media for delete to authenticated using (public.is_admin());

drop policy if exists audit_admin_select on public.audit_logs;
create policy audit_admin_select on public.audit_logs for select to authenticated using (public.is_admin());

insert into storage.buckets(id,name,public) values('project-mov','project-mov',false) on conflict(id) do update set public=false;
drop policy if exists mov_select on storage.objects;
create policy mov_select on storage.objects for select to authenticated using (bucket_id='project-mov');
drop policy if exists mov_insert on storage.objects;
create policy mov_insert on storage.objects for insert to authenticated with check (bucket_id='project-mov' and public.is_admin());
drop policy if exists mov_delete on storage.objects;
create policy mov_delete on storage.objects for delete to authenticated using (bucket_id='project-mov' and public.is_admin());
