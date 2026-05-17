"""Structural tests: ResponsePublisherProtocol is satisfied by both implementations."""

from unittest.mock import MagicMock

from telegram import Bot

from bot.publisher import (
    FakeResponsePublisher,
    ResponsePublisher,
    ResponsePublisherProtocol,
)


def test_response_publisher_satisfies_protocol():
    bot = MagicMock(spec=Bot)
    assert isinstance(ResponsePublisher(bot=bot), ResponsePublisherProtocol)


def test_fake_response_publisher_satisfies_protocol():
    assert isinstance(FakeResponsePublisher(), ResponsePublisherProtocol)
