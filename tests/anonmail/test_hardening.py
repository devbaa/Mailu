"""Tests for the anonmail hardening changes: quota enforcement, input
length validation and alias localpart generation."""

import re

from mailu import models, utils

TOKEN = 'e' * 32


def _setup(app, create_user_and_token, grant_domain_access, max_aliases=-1):
    d = models.Domain(name='example.com', anonmail_enabled=True, max_aliases=max_aliases)
    models.db.session.add(d)
    models.db.session.commit()

    user, token = create_user_and_token(email='hard@example.com', token_str=TOKEN)
    grant_domain_access('example.com', user=user)
    return d, user


class TestQuotaEnforcement:

    def test_api_rejects_creation_when_quota_reached(self, app, client, create_user_and_token, grant_domain_access):
        with app.app_context():
            d, user = _setup(app, create_user_and_token, grant_domain_access, max_aliases=1)
            headers = {'Authentication': f'{user.email}:{TOKEN}'}

            rv = client.post('/api/alias/random/new', headers=headers, json={})
            assert rv.status_code == 201

            rv = client.post('/api/alias/random/new', headers=headers, json={})
            assert rv.status_code == 409
            assert models.Alias.query.count() == 1

    def test_api_unlimited_quota_still_works(self, app, client, create_user_and_token, grant_domain_access):
        with app.app_context():
            d, user = _setup(app, create_user_and_token, grant_domain_access, max_aliases=-1)
            headers = {'Authentication': f'{user.email}:{TOKEN}'}

            for _ in range(3):
                rv = client.post('/api/alias/random/new', headers=headers, json={})
                assert rv.status_code == 201


class TestInputValidation:

    def test_api_rejects_overlong_hostname(self, app, client, create_user_and_token, grant_domain_access):
        with app.app_context():
            d, user = _setup(app, create_user_and_token, grant_domain_access)
            headers = {'Authentication': f'{user.email}:{TOKEN}'}

            rv = client.post(f'/api/alias/random/new?hostname={"a" * 300}.com', headers=headers, json={})
            assert rv.status_code == 400
            assert models.Alias.query.count() == 0

    def test_api_rejects_overlong_note(self, app, client, create_user_and_token, grant_domain_access):
        with app.app_context():
            d, user = _setup(app, create_user_and_token, grant_domain_access)
            headers = {'Authentication': f'{user.email}:{TOKEN}'}

            rv = client.post('/api/alias/random/new', headers=headers, json={'note': 'x' * 300})
            assert rv.status_code == 400
            assert models.Alias.query.count() == 0

    def test_api_rejects_non_string_note(self, app, client, create_user_and_token, grant_domain_access):
        with app.app_context():
            d, user = _setup(app, create_user_and_token, grant_domain_access)
            headers = {'Authentication': f'{user.email}:{TOKEN}'}

            rv = client.post('/api/alias/random/new', headers=headers, json={'note': {'nested': 'object'}})
            assert rv.status_code == 400
            assert models.Alias.query.count() == 0


class TestLocalpartGeneration:

    def test_hostname_localpart_format(self):
        localpart = utils.generate_anonymous_alias_localpart('www.example.com')
        assert re.fullmatch(r'example\.[a-z]+\d{4}', localpart), localpart

    def test_localpart_never_contains_none(self, monkeypatch):
        # If no dictionary words are available the random part must fall
        # back to a random token instead of the string 'None'
        monkeypatch.setattr(utils, 'anonymous_alias_words', lambda: ())
        localpart = utils.generate_anonymous_alias_localpart('www.example.com')
        assert 'None' not in localpart
        assert localpart.startswith('example.')
        assert len(localpart) > len('example.') + 8

    def test_localpart_respects_length_limit(self):
        long_label = 'a' * 63
        localpart = utils.generate_anonymous_alias_localpart(f'{long_label}.com')
        assert len(localpart) <= 64
        assert '.' in localpart
