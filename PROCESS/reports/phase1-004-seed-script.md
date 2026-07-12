## Result: ✅ DoD met

Gate: `supabase db reset` ✅ (clean, auto-runs migration + seed every time) · real query verification ✅ via `supabase-py`: 3 deals present with correct name/stage/status, Deal A's contact/document/milestones/task/dd_items/meeting_note all match the worked example, 1 seeded user (Priya Sharma, Partner) · demo user sign-in ✅ (`sign_in_with_password`, real JWT returned)

Deviations from spec: none in the seeded data itself. "Valuation — under review" from the Section 3.3 worked example was deliberately NOT seeded as a `tasks` row — it isn't a task, it maps to the Analysis tab's pricing status (ux-ui-spec.md's own worked-example table says so explicitly), and there's no pricing/analysis table in the 8-model schema to hold it. Not inventing a field/table outside the given schema for this.

Risks/found-and-fixed: the demo user's `auth.users` insert initially left several `*_token`/`email_change*` columns NULL, which look harmless (schema shows some with `''` defaults) but broke every password sign-in with an opaque 500 until root-caused from the auth container's own logs (`docker logs supabase_auth_Kuvera_Project`) — see D-006. Anyone adding a second seeded user later must copy the same explicit column list, not just the columns that seemed relevant at a glance.
