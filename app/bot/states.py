from aiogram.fsm.state import State, StatesGroup


class IdentityForm(StatesGroup):
    full_name = State()
    mobile = State()
    birth_date = State()
    return_date = State()
    consulate = State()
    identity_document = State()
    tazkira = State()
    companion_choice = State()
    companion_name = State()
    companion_mobile = State()
    confirm = State()
    receipt = State()


class KhodnevisForm(StatesGroup):
    full_name = State()
    mobile = State()
    document_type = State()
    amayesh = State()
    passport_first = State()
    passport_renewal = State()
    residence_renewal = State()
    own_mobile = State()
    confirm = State()
    receipt = State()
