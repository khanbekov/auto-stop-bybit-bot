import logging

import ccxt
from aiogram import Router, Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from ccxt import AuthenticationError

from src.models.position_couple import PositionCouple
from src.services.bybit_gate import BybitGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class BybitInteraction:
    router: Router = Router()

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: BybitGate):
        self.db = db
        self.bot = bot
        self.dp = dispatcher
        self.exc_gate = exchange_gate
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.check_keys, Command("check_keys"))
        self.router.message.register(self.get_positions, Command("positions"))

    async def check_keys(self, message: Message):
        try:
            result = self.db.get_user_keys(tg_user_id=message.from_user.id)

            if len(result) == 0:
                await message.reply(text="Ключи не найдены.")
                return

            if free_balance := self.exc_gate.check_connection(message.from_user.id):
                await message.reply(text=f"Удалось подключиться к API. Ключи корректны."
                                         f" Текущий свободный баланс: {free_balance} USDT")
                return
            await message.reply(text="Не удалось подключиться к API.")
        except AuthenticationError as e:
            await message.reply(text="Не удалось подключиться к API. Некорректные ключи.")
            logger.warning(f"AuthenticationError on check_keys() {e}", exc_info=True)
        except Exception as e:
            await message.reply(text="Не удалось проверить ключи, попробуйте ещё раз и проверьте "
                                     "правильность введенных ключей.")
            logger.warning(f"Error on set_new_keys() {e}", exc_info=True)

    async def get_user_keys(self, message: Message):
        try:
            result = self.db.get_user_keys(tg_user_id=message.from_user.id)

            if len(result) == 0:
                await message.reply(text="Ключи не найден.")
                return
            await message.reply(text=f"Ключи:\n"
                                     f"- Public: {result[0].public_key}\n"
                                     f"- Private {result[0].private_key[:4] + '*' * (len(result[0].private_key) - 4)}")
        except Exception as e:
            await message.reply(text="Не удалось получить ключи, попробуйте ещё раз.")
            logger.warning(f"Error on get_user_keys() {e}", exc_info=True)

    async def get_positions(self, message: Message):
        try:
            positions = self.exc_gate.get_current_positions_as_dict(message.from_user.id)

            answer = 'Symbol  :  Contracts  :  ROI  :  PnL\n ' \
                     '--------------------------'
            for symbol, position in positions.items():
                answer += f'\n{symbol} : {position["contracts"]} : {position["roi"]:.3f}% : {position["pnl"]}'

            await message.reply(text=f"Текущие позиции:\n\n{answer}")
        except Exception as e:
            await message.reply(text="Не удалось получить позиции, попробуйте ещё раз.")
            logger.warning(f"Error on get_positions() {e}", exc_info=True)