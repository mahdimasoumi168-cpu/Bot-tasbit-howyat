from aiogram.fsm.storage.base import StorageKey

from app.bot.sqlite_fsm import SQLiteFSMStorage


async def test_fsm_state_and_form_data_survive_storage_recreation(tmp_path):
    path = tmp_path / "fsm.db"
    key = StorageKey(bot_id=999, chat_id=123, user_id=123)

    first = SQLiteFSMStorage(str(path))
    await first.set_state(key, "IdentityForm:mobile")
    await first.set_data(key, {"full_name": "احمد محمدی", "mobile": "09123456789"})
    await first.close()

    second = SQLiteFSMStorage(str(path))
    assert await second.get_state(key) == "IdentityForm:mobile"
    assert await second.get_data(key) == {
        "full_name": "احمد محمدی",
        "mobile": "09123456789",
    }

    await second.set_state(key, None)
    await second.set_data(key, {})
    assert await second.get_state(key) is None
    assert await second.get_data(key) == {}
    await second.close()
