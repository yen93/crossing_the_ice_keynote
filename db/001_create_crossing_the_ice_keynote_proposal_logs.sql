-- Audit/dedup log for the standalone Crossing the Ice Keynote (James
-- Castrission) proposal automation. Independent of
-- public.interactive_keynote_proposal_logs and
-- public.proposal_demo_notes_email_logs — this pipeline never reads or
-- writes either of those tables.

create table public.crossing_the_ice_keynote_proposal_logs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  message_id text unique,
  is_processed boolean not null default false,
  status text,
  error_message text,
  proposal_link text,
  processed_at timestamptz,
  client_org text,
  event_date text,
  logo_replaced boolean not null default false
);

comment on table public.crossing_the_ice_keynote_proposal_logs is
  'Audit/dedup log for the standalone Crossing the Ice Keynote (James Castrission) proposal automation. Independent of public.interactive_keynote_proposal_logs and public.proposal_demo_notes_email_logs.';

alter table public.crossing_the_ice_keynote_proposal_logs enable row level security;
