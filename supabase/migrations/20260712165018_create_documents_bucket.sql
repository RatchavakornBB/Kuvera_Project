-- Private Storage bucket for deal documents. Not public — deal documents are
-- confidential, accessed only via the backend's service_role key (Section 5.5:
-- secrets only in .env, backend-mediated access, no direct public URLs).
insert into storage.buckets (id, name, public)
values ('deal-documents', 'deal-documents', false);

grant usage on schema storage to service_role;
grant select, insert, update, delete on storage.objects, storage.buckets to service_role;
