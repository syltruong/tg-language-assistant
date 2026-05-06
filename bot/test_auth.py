from bot.auth import AllowlistAuthorizer, Authorizer, FakeAuthorizer


class TestFakeAuthorizer:
    def test_allow_true_authorizes_any_user(self):
        auth = FakeAuthorizer(allow=True)
        assert auth.is_authorized(999)

    def test_allow_false_denies_any_user(self):
        auth = FakeAuthorizer(allow=False)
        assert not auth.is_authorized(999)

    def test_default_is_allow(self):
        auth = FakeAuthorizer()
        assert auth.is_authorized(0)


class TestAllowlistAuthorizer:
    def test_empty_allowlist_permits_everyone(self):
        auth = AllowlistAuthorizer(allowlist=set())
        assert auth.is_authorized(12345)

    def test_listed_user_is_authorized(self):
        auth = AllowlistAuthorizer(allowlist={123, 456})
        assert auth.is_authorized(123)

    def test_unlisted_user_is_denied(self):
        auth = AllowlistAuthorizer(allowlist={123})
        assert not auth.is_authorized(999)


class TestAuthorizerProtocol:
    def test_fake_satisfies_protocol(self):
        assert isinstance(FakeAuthorizer(), Authorizer)

    def test_allowlist_satisfies_protocol(self):
        assert isinstance(AllowlistAuthorizer(allowlist=set()), Authorizer)
