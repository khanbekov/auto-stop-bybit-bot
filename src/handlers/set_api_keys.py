import logging

from aiogram import Router, Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from src.services.bybit_gate import BybitGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class SetKeysHandler:
    router: Router = Router()

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: BybitGate):
        self.db = db
        self.bot = bot
        self.dp = dispatcher
        self.exc_gate = exchange_gate
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.set_new_keys, Command("set_keys"))
        self.router.message.register(self.get_user_keys, Command("get_keys"))

    def register_message_handlers(self, dp: Dispatcher):
        """
        Method used to register all message handlers for the bot. Each command or regex pattern is mapped to a specific
        handler function.

        :param dp: Dispatcher - Dispatcher instance
        :return: None
        """
        ...

    async def set_new_keys(self, message: Message):
        try:
            _, public, private = message.text.split()

            self.db.set_user_api_keys(message.from_user.id, public, private)
            self.exc_gate.set_keys(message.from_user.id, public, private)
            await message.reply(text="Ключи успешно установлены.")
        except Exception as e:
            await message.reply(text="Не удалось установить ключи, попробуйте ещё раз.")
            logger.warning(f"Error on set_new_keys() {e}", exc_info=True)

    async def get_user_keys(self, message: Message):
        try:
            result = self.db.get_user_keys(tg_user_id=message.from_user.id)

            if len(result) == 0:
                await message.reply(text="Ключи не найдены.")
                return
            await message.reply(text=f"Ключи:\n"
                                     f"- Public: {result[0].public_key}\n"
                                     f"- Private: {result[0].private_key[:4] + '*' * (len(result[0].private_key) - 4)}")
        except Exception as e:
            await message.reply(text="Не удалось получить ключи, попробуйте ещё раз.")
            logger.warning(f"Error on get_user_keys() {e}", exc_info=True)
