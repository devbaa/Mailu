from mailu import utils


class TestAnonymousAliasLocalpart:
    """Tests for anonymous alias localpart generation"""

    def test_generate_anonymous_alias_localpart_with_hostname(self):
        """Test anonymous alias generation with hostname"""
        result = utils.generate_anonymous_alias_localpart(hostname='www.example.com')
        assert isinstance(result, str)
        assert '.' in result  # Should have format: hostname_prefix.word + 4 digits
        prefix, word = result.split('.', 1)
        assert prefix == 'example'
        assert word[:-4].isalpha()
        assert word[:-4].islower()
        assert word[-4:].isdigit()
        assert 5 <= len(word[:-4]) <= 10

    def test_generate_anonymous_alias_localpart_without_hostname(self):
        """Test anonymous alias generation without hostname"""
        result = utils.generate_anonymous_alias_localpart()
        assert isinstance(result, str)
        # Should be a random token (not a word)
        assert len(result) > 0

    def test_generate_anonymous_alias_localpart_consistency(self):
        """Test that generate_anonymous_alias_localpart returns different words (most of the time)"""
        words = [utils.generate_anonymous_alias_localpart(hostname='www.example.com') for _ in range(10)]
        # At least some words should be different
        assert len(set(words)) > 1
