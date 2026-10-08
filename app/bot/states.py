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


class AdminForm(StatesGroup):
    case_lookup = State()
    send_message = State()
    set_card_number = State()
    set_card_holder = State()
    set_price = State()
    user_search = State()
    operator_add = State()
    operator_permission = State()
    operator_remove = State()


class RetryReceiptForm(StatesGroup):
    receipt = State()


class SupportForm(StatesGroup):
    message = State()
