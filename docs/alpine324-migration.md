# Mailu 2024.06: coordinated Alpine 3.24 security migration

**Status: integration planning / not deployable.** This branch starts from upstream `2024.06` at `eb012283`. The existing stable images are not modified yet. The diagnostic workflow never pushes images.

## Target package baseline (Alpine 3.24-stable APKBUILD, checked 21 November 2026)

| Package | Target | Why it matters |
|---|---|---|
| Alpine | `ghcr.io/mailu/alpine:3.24.3` | Base for all Mailu-derived images; mirror and lock digest before release |
| nginx + nginx-mod-mail | `>=1.30.7-r0` | HTTP/2/HTTP/3, resolver and mail proxy vulnerabilities |
| Dovecot + plugins | `>=2.4.5-r0` | IMAP/POP3/submission/ManageSieve vulnerabilities; requires 2.4 migration |
| PHP 8.3 + FPM | `>=8.3.37-r0` | Keep PHP 8.3, security-patched |
| Python | Alpine 3.24 gives `3.14.10` | Revalidate **all** stable Python dependencies and binary wheels |
| Postfix | `3.11.7` | Config, queue and TLS behavior |
| Rspamd | `4.0.1` | Rules, modules, DKIM, fuzzy/redis and spam/ham learning |

These are desired inputs, **not verified versions inside built images**.

## The dependency graph

```text
Alpine 3.24 mirror and digest
  -> build core/base (Python 3.14 pinned wheels + Snuffleupagus compiled for PHP 8.3)
      -> admin + setup + auxiliary services
      -> front nginx 1.30.7 + Dovecot 2.4.5 login proxy
      -> imap Dovecot 2.4.5 mailbox backend
      -> webmail nginx 1.30.7 + PHP 8.3.37/FPM + extensions
      -> Postfix 3.11.7 and Rspamd 4.0.1
  -> all images must pass end-to-end integration before an RC is published
```

## Workstreams and merge gates

### 1. Base and Python (blocking everything)

- [ ] Mirror `3.24.3` via `.github/workflows/mirror.yml` and pin a verified multiarch digest.
- [ ] Build `core/base` on amd64 and arm64 (armv7 only if supported).
- [ ] Resolve stable `requirements-prod.txt` against Python 3.14 without wholesale replacement from master; inspect `cryptography`, `greenlet`, `mariadb`, `psycopg2-binary`, `aiohttp`, `cffi`, `bcrypt`, `pycares` and `uvloop` compatibility.
- [ ] Compile Snuffleupagus 0.10.0 (or backport narrowly) against Alpine 3.24 PHP 8.3; verify dynamic loading and PHP startup.
- [ ] Verify PHP 8.3 extensions against Alpine 3.24, including `php83-pspell`, GPG, enchant/aspell and database connectors.

### 2. Front nginx and webmail PHP

- [ ] Pin nginx and `nginx-mod-mail` from the **same** Alpine 3.24 repository/version.
- [ ] Test `nginx -t` across TLS modes, HTTP/2, IPv4/IPv6, MAIL_AUTH, SMTP mail proxy, and PROXY protocol.
- [ ] Pin PHP 8.3.37+ and FPM, confirm all extensions load, run Roundcube + SnappyMail smoke tests.
- [ ] Coordinate upstream PRs [#4214](https://github.com/Mailu/Mailu/pull/4214) and [#4215](https://github.com/Mailu/Mailu/pull/4215) without cherry-picking their Alpine 3.22 base lines.

### 3. Dovecot 2.4 frontend

- [ ] Convert `core/nginx/dovecot/proxy.conf`: settings version, TLS/SSL keys, protocol map, passdb Lua and auth worker, all listener ports and trusted HAProxy networks.
- [ ] Port `core/nginx/dovecot/login.lua`: 2.4 HTTP client API, request headers, app-token logins, auth failure codes, backend proxy responses. Maintain stable admin API contracts.
- [ ] Validate `doveconf -n` and `luac -p` **in the built image** for all supported settings.

### 4. Dovecot 2.4 mailbox backend

- [ ] Convert `core/dovecot/conf/dovecot.conf`: dict auth to Lua, quota/count/clone, maildir, FTS flatcurve, compression, LMTP, Sieve, managesieve.
- [ ] Preserve stable `/mail/<email>` storage, mail UID/GID 8, existing quota and Sieve semantics. **Do not copy** `master`'s sharded per-user UID/chroot migration without an explicit data migration plan.
- [ ] Integrate opt-in admin compatibility work from [fork PR #5](https://github.com/devbaa/Mailu/pull/5) only after reviewing its behavior; verify disabled users and malformed address handling.
- [ ] Test Dovecot's dict transport to Podop for quota and Sieve; account for 2.4 dict transaction expiry fields and status handling.
- [ ] Compile all Sieve scripts using `sievec`. Test spam/ham, vacation and mailbox subscriptions, including IMAPSieve and ManageSieve.

### 5. Other images

- [ ] Build/test smtp (Postfix), antispam (Rspamd 4), resolver (Unbound), admin, setup, oletools, fetchmail, webdav/Radicale, none, and image tooling.
- [ ] Inspect every APK package name, Python module import, PHP extension load, runtime user/group, permissions and health check.
- [ ] Test SQLite/MySQL/PostgreSQL admin-backed operations where supported.

### 6. Full stack and release safety

- [ ] Run core/filters/webmail/API compose suites; test incoming SMTP -> LMTP, submission, IMAP, POP3, Sieve, quotas, password denial, rate limits and TLS.
- [ ] Create disposable production-like copies of databases + mailbox volumes + Sieve/filter state. Compare mailbox counts/UIDs/flags/subscriptions and quota before/after.
- [ ] Rehearse restoration of the **entire** original database/mailbox state and images. Downgrade of an already modified mail volume without backup is not assumed safe.
- [ ] Validate every runtime APK version, lock image digests, publish **candidate** tags only, and approve deployment separately. No automatic promotion to `2024.06` or `latest`.

## Diagnostic builds

The workflow `.github/workflows/alpine324-compatibility.yml` is manual (`workflow_dispatch`), does not use credentials, and does **not** publish images. It injects the 3.24 base through the pre-existing `ARG DISTRO` and executes a selected build target. The first failure is expected to expose dependency incompatibilities; don't mistake the presence of the workflow for a tested migration.

No Docker runtime or direct network clone is available in the current assistant environment. GitHub Actions must run the actual builds.

## Coordination and scope

- [fork PR #4](https://github.com/devbaa/Mailu/pull/4) applies only to `master`, not this migration.
- [fork PR #5](https://github.com/devbaa/Mailu/pull/5) is a partial stable auth contract scaffold, not complete Dovecot 2.4.
- [upstream PR #4214](https://github.com/Mailu/Mailu/pull/4214) and [#4215](https://github.com/Mailu/Mailu/pull/4215) target Alpine 3.22; this candidate targets 3.24.
- **Never merge or deploy this branch until all blocking gates have passed.**
