"""UserSession: slot map methods are removed."""

from bot.session import UserSession


def test_get_slot_id_does_not_exist():
    session = UserSession({})
    assert not hasattr(session, "get_slot_id")


def test_set_slot_id_does_not_exist():
    session = UserSession({})
    assert not hasattr(session, "set_slot_id")
