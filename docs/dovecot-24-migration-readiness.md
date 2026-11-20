# Dovecot 2.4 migration readiness for Mailu 2024.06

**NOT READY FOR PRODUCTION.** This branch deliberately does not install Dovecot 2.4, change either live Dovecot config, touch persistent mail data, or change existing 2.3 endpoint replies.

## What is prepared

The existing admin internal API supports an opt-in `?format=2.4` representation for the Dovecot passdb and userdb responses. This is meant for future 2.4 Lua auth and is **not enabled by current Dovecot**.

- `/internal/dovecot/passdb/<email>?format=2.4`: `password: ""` instead of JSON null, with the existing `nopassword` and trusted-network fields preserved.
- `/internal/dovecot/userdb/<email>?format=2.4`: `uid: 8`, `gid: 8`, `home: /mail/<email>`, and `quota_storage_size` (string), preserving Mailu 2024.06's Maildir root and mailbox ownership.
- No query parameter: original 2.3 response stays unchanged.

## Current blockers

1. **Packaging**: Alpine 3.22 packages Dovecot 2.4.1, not security-fixed >=2.4.5. Do not mix Alpine 3.24 packages into Alpine 3.22 without a verified dependency/ABI plan.
2. **Front**: Dovecot 2.4 requires `dovecot_config_version`/`dovecot_storage_version`, new Lua passdb configuration, rewritten SSL and protocol syntax; the existing 2.3 proxy config cannot be reused. The nginx mail proxy and IMAP/POP3/SMTP/ManageSieve listeners require test coverage.
3. **Backend**: migrate old `passdb/userdb dict` to Lua, quota and quota-clone to 2.4, Sieve/pigeonhole and FTS directives, compression, and 2.4 plugin syntax. Preserve `/mail/<email>` rather than copying `master`'s sharded/chroot layout. Existing mailbox UIDs/GIDs are 8, not `master`'s per-user IDs.
4. **Podop**: quota and Sieve dict-proxy calls must be tested against 2.4, including transaction begin frames with optional expiry.
5. **Admin/internal**: the new Lua script must explicitly request `?format=2.4`, and authenticated access must be limited to the internal subnet. Validate disabled accounts and malformed addresses.
6. **Release coordination**: #4214 (nginx/base) and #4215 (PHP/base) overlap on the shared base. Avoid merging unrelated base changes into this PR.

## Required test gates before removing the draft flag

- Build *both* front and backend with security-patched Dovecot >=2.4.5 and the chosen Alpine base; verify actual APK versions inside images.
- Render both configurations for TLS and no-TLS, optional ManageSieve, SMTP submission, IPv4/IPv6, and all FULL_TEXT_SEARCH/compression permutations; run `doveconf -c ... -n` inside the exact image.
- Compile every global Sieve script with `sievec`; validate Lua syntax and auth against enabled/disabled users, app passwords, invalid credentials and HTTP API failure.
- Test SMTP submission, inbound Postfix -> LMTP delivery, IMAP/POP3, ManageSieve, quotas/usage reporting, full-text search, spam/ham learning and vacation replies.
- Mount a **disposable copy** of an existing 2.3 mailbox; compare message count, UIDs, flags, subscriptions, folders, ACLs and file ownership before/after. Do not rewrite the production mailbox in place.
- Verify rollback to 2.3 with a separately preserved mailbox snapshot; do not assume indexes or metadata downgradability.
- Re-run official `tests/compose/core`, `tests/compose/filters`, and webmail integration suites.

Small initial contract test:
```sh
python3 -m unittest discover -s tests -p 'test_dovecot24_compat.py'
```

This preparatory change intentionally **does not claim to make Mailu 2024.06 run Dovecot 2.4**.
