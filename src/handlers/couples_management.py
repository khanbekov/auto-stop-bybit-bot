import logging
import re

from aiogram import Router, Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command

from src.keyboards.keyboards import main_markup
from src.services.exchange_gate import ExchangeGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class CouplesManagement:
    router: Router = Router()

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: ExchangeGate):
        self.db = db
        self.bot = bot
        self.dp = dispatcher
        self.exc_gate = exchange_gate
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.create_new_couple, Command("new"))
        self.router.message.register(self.get_couples, Command("stops"))
        self.router.message.register(self.remove_couple, Command("remove"))
        self.router.message.register(self.change_couple_roi_stop_value, Command("change"))


    async def create_new_couple(self, message: Message):
        try:
            tickers = message.text.split()[1:-1]
            roi_stop_value = float(message.text.split()[-1].strip().replace('%', ''))

            exchange = self.db.get_selected_exchange(message.from_user.id)
            if exchange is None:
                await message.reply(text="Не выбрана текущая биржа. Пожалуйста, укажите её `/exchange &lt;название&gt;`")
                return

            pattern = r'^\w{1,}$'
            for i, ticker in enumerate(tickers):
                if re.match(pattern, ticker):
                    tickers[i] = f"{ticker.upper()}/USDT:USDT"

            current_roi = await self.exc_gate.get_sum_roi_for_couple(message.from_user.id,
                                                                     exchange=exchange.exchange,
                                                                     tickers=tickers)
            self.db.add_couple(
                tg_user_id=message.from_user.id,
                tickers=tickers,
                exchange=exchange.exchange,
                roi_stop_value=roi_stop_value,
                check_profit=roi_stop_value > current_roi
            )
            await message.reply(text=f"Добавлен стоп [{', '.join(tickers)}], c ROI {roi_stop_value}%.",
                                reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось добавить стоп, попробуйте ещё раз.")
            logger.warning(f"Error on create_new_couple() {e}", exc_info=True)

    async def get_couples(self, message: Message):
        try:
            couples = self.db.get_user_couples(message.from_user.id)

            answer = 'Id : Exchange : Tickers : Stop ROI : Direction\n' \
                     '----------------------------------------------'
            for key, couple in couples.items():
                answer += f'\n{key} : {couple.exchange} : ' \
                          f'{", ".join(couple.tickers).replace("/USDT:USDT", "")}  :  ' \
                          f'{couple.roi_stop_value}% :  {"🠕" if couple.check_profit else "🠗"}'

            await message.reply(text=f"Текущие стопы:\n\n<code>{answer}</code>", reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось получить стопы, попробуйте ещё раз.")
            logger.warning(f"Error on get_couples() {e}", exc_info=True)

    async def remove_couple(self, message: Message):
        try:
            couple_id = int(message.text.split()[-1].strip())

            removed_couple, removed_tickers = self.db.remove_couple(message.from_user.id, couple_id)

            if removed_couple is None:
                await message.reply(f"Не найден стоп с id {couple_id}.")
                return

            answer = 'Id : Tickers\n' \
                     '--------------------------'
            tickers = [ticker.ticker for ticker in removed_tickers]
            answer += f'\n{removed_couple.id}   :   {" ".join(tickers)}'

            await message.reply(text=f"Удален стоп:\n\n{answer}", reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось удалить стоп, попробуйте ещё раз.")
            logger.warning(f"Error on remove_couple() {e}", exc_info=True)

    async def change_couple_roi_stop_value(self, message: Message):
        try:
            couple_id = int(message.text.split()[-2].strip())
            roi_stop_value = float(message.text.split()[-1].strip().replace('%', ''))

            couple = self.db.get_couple(message.from_user.id, couple_id)

            if couple is None:
                await message.reply(f"Не найден стоп с id {couple_id}.")
                return

            current_roi = await self.exc_gate.get_sum_roi_for_couple(message.from_user.id, couple.exchange,
                                                                     couple.tickers)
            self.db.update_couple_roi_stop_value(
                tg_user_id=message.from_user.id,
                couple_id=couple_id,
                roi_stop_value=roi_stop_value,
                check_profit=roi_stop_value > current_roi
                # check_profit=roi_stop_value > current_roi if current_roi is not None else roi_stop_value > 0
            )
            couple = self.db.get_couple(message.from_user.id, couple_id)

            if couple is None:
                await message.reply(f"Не найден стоп с id {couple_id}.")
                return

            await message.reply(text=f"Обновлен стоп: [{', '.join(couple.tickers)}], c ROI {couple.roi_stop_value}%.",
                                reply_markup=main_markup)
        except Exception as e:
            await message.reply(text="Не удалось обновить стоп, попробуйте ещё раз.")
            logger.warning(f"Error on change_couple_roi_stop_value() {e}", exc_info=True)
