import logging

import ccxt
from aiogram import Router, Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from src.keyboards.keyboards import main_markup
from src.services.exchange_gate import ExchangeGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class SetKeysHandler:
    router: Router = Router()

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: ExchangeGate):
        self.db = db
        self.bot = bot
        self.dp = dispatcher
        self.exc_gate = exchange_gate
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.set_new_keys, Command("set_keys"))
        self.router.message.register(self.get_user_keys, Command("get_keys"))
        self.router.message.register(self.set_exchange, Command("exchange"))
        self.router.message.register(self.set_exchange, Command("exc"))

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
            _, exchange, public, private = message.text.split()
            exchange = exchange.strip().lower()

            if exchange not in ccxt.exchanges:
                await message.reply(text=f"Не найдена биржа {exchange}.")
                return

            self.db.set_user_api_keys(message.from_user.id, exchange, public, private)
            self.exc_gate.set_keys(message.from_user.id, exchange, public, private)
            await message.reply(text="Ключи успешно установлены.", reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось установить ключи, попробуйте ещё раз.")
            logger.warning(f"Error on set_new_keys() {e}", exc_info=True)

    async def get_user_keys(self, message: Message):
        try:
            result = self.db.get_all_user_keys(tg_user_id=message.from_user.id)

            if len(result) == 0:
                await message.reply(text="Ключи не найдены.")
                return
            answer = f"Ключи:\n"
            for key_pair in result:
                answer += f"{key_pair.exchange}\n" \
                f"- Public: {key_pair.public_key}\n" \
                f"- Private: {key_pair.private_key[:4] + '*' * (len(key_pair.private_key) - 4)}\n\n"

            await message.reply(text=answer, reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось получить ключи, попробуйте ещё раз.")
            logger.warning(f"Error on get_user_keys() {e}", exc_info=True)

    async def set_exchange(self, message: Message):
        try:
            if len(message.text.split(' ')) == 1:
                selected_exchange = self.db.get_selected_exchange(message.from_user.id)
                if selected_exchange is None:
                    await message.reply(text="Не выбрана текущая биржа. Пожалуйста, укажите её "
                                             "`/exchange &lt;название&gt;`")
                else:
                    await message.reply(text=f"Текущая биржа: {selected_exchange.exchange}", reply_markup=main_markup)
                return

            _, exchange = message.text.split()

            exchange = exchange.strip().lower()

            if exchange not in ccxt.exchanges:
                await message.reply(text=f"Не найдена биржа {exchange}.")
                return

            self.db.set_selected_exchange(message.from_user.id, exchange)
            await message.reply(text=f"Установлена биржа {exchange} в качестве текущей.", reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось проверить/установить текущую биржа, пожалуйста, попробуйте ещё раз.")
            logger.warning(f"Error on set_exchange() {e}", exc_info=True)
