import logging

import ccxt
from aiogram import Router, Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from ccxt import AuthenticationError

from src.keyboards.keyboards import main_markup
from src.models.position_couple import PositionCouple
from src.services.exchange_gate import ExchangeGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class ExchangeInteraction:
    router: Router = Router()

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: ExchangeGate):
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

            selected_exchange = self.db.get_selected_exchange(message.from_user.id)
            if selected_exchange is None:
                await message.reply(text="Не выбрана текущая биржа. Пожалуйста, укажите её `/exchange &lt;название&gt;`")
                return

            result = self.db.get_user_keys_for_exchange(tg_user_id=message.from_user.id,
                                                        exchange=selected_exchange.exchange)

            if len(result) == 0:
                await message.reply(text="Ключи не найдены.")
                return

            free_balance = self.exc_gate.check_connection(message.from_user.id,
                                                          exchange=selected_exchange.exchange)
            if free_balance is not None:
                await message.reply(text=f"Удалось подключиться к API. Ключи корректны."
                                         f" Текущий свободный баланс: {free_balance} USDT", reply_markup=main_markup)
                return
            await message.reply(text="Не удалось подключиться к API.")
        except AuthenticationError as e:
            await message.reply(text="Не удалось подключиться к API. Некорректные ключи.")
            logger.warning(f"AuthenticationError on check_keys() {e}", exc_info=True)
        except Exception as e:
            await message.reply(text="Не удалось проверить ключи, попробуйте ещё раз и проверьте "
                                     "правильность введенных ключей.")
            logger.warning(f"Error on check_keys() {e}", exc_info=True)

    async def get_positions(self, message: Message):
        try:
            selected_exchange = self.db.get_selected_exchange(message.from_user.id)
            if selected_exchange is None:
                await message.reply(text="Не выбрана текущая биржа. Пожалуйста, укажите её `/exchange &lt;название&gt;`")
                return

            positions = self.exc_gate.get_current_positions_as_dict_on_exchange(
                message.from_user.id, exchange=selected_exchange.exchange)

            answer = 'Symbol  :  Contracts  :  ROI  :  PnL\n' \
                     '------------------------------------'
            for symbol, position in positions.items():
                answer += f'\n{symbol} : {position["contracts"]} : {position["roi"]:.3f}% : ' \
                          f'{position["pnl"]}'

            await message.reply(text=f"Текущие позиции:\n\n<code>{answer}</code>", reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось получить позиции, попробуйте ещё раз.")
            logger.warning(f"Error on get_positions() {e}", exc_info=True)
