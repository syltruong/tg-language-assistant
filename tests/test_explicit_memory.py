"""End-to-end acceptance test for the explicit memory capability.

Exercises the real SQLite path across a simulated restart. This is the whole
point of the feature: anything kept has to still be there afterwards.
"""

import pytest

from bot.insights import SqliteInsightRepository
from bot.keyboard import SAVE, build_action_keyboard
from bot.localizer import Localizer
from bot.storage.db import Database
from bot.triggers.save import SaveTrigger
from bot.triggers.saved_list import SavedListTrigger
from tests.factories import make_callback_update, make_context, make_update


@pytest.mark.asyncio
async def test_a_kept_turn_survives_a_bot_restart(tmp_path):
    db_path = tmp_path / "bot.db"

    # First run — the user deep-dives a message and keeps the result.
    database = Database(path=db_path)
    await database.connect()
    save = SaveTrigger(repository=SqliteInsightRepository(database=database))
    tap = make_callback_update(
        callback_data=SAVE,
        message_id=77,
        reply_text="Je suis allé au marché",
        slot_text="'allé' agrees with the subject",
    )
    tap.callback_query.message.reply_markup = build_action_keyboard()
    await save.handle(tap, make_context(user_data={"slot_actions": {77: "correct"}}))
    await database.close()

    # Restart — a brand-new connection and an empty Session, as after a deploy.
    database = Database(path=db_path)
    await database.connect()
    saved_list = SavedListTrigger(
        repository=SqliteInsightRepository(database=database), localizer=Localizer()
    )
    request = make_update()
    await saved_list.handle(request, make_context())
    await database.close()

    listed = request.message.reply_text.call_args.args[0]
    assert "Je suis allé au marché" in listed
    assert "correct" in listed
