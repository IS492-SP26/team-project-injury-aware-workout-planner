-- Optional: run in Supabase SQL editor if the table already exists without this column.
alter table public.youtube_videos add column if not exists youtube_video_id text;

create index if not exists youtube_videos_user_video_id_idx
  on public.youtube_videos (user_id, youtube_video_id)
  where youtube_video_id is not null;
