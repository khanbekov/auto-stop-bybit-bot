import asyncio
import logging
import time
from typing import NoReturn

from aiogram import Bot, Dispatcher

from src.models.position_couple import CoupleWithTickers
from src.services.bybit_gate import BybitGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class StopsHandler:

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: BybitGate):
        self.db = db
        self.bot = bot
        self.dp = dispatcher
        self.exc_gate = exchange_gate

    async def send_realized_stops_message(self, couple: CoupleWithTickers, current_roi: float):
        await self.bot.send_message(
            couple.tg_user_id,
            f'Закрыта позиция по тикерам: {", ".join(couple.tickers)}.\n'
            f'Достигнут ROI {current_roi:.3f}%'
        )

    async def check_stops(self):
        all_couples = self.db.get_all_couples()
        for tg_user_id, user_couples in all_couples.items():
            user_positions = self.exc_gate.get_current_positions_as_dict(tg_user_id=tg_user_id)
            for couple_id, couple in user_couples.items():
                if roi_sum := await self.exc_gate.get_roi_for_couple_with_positions(
                        tg_user_id=tg_user_id,
                        tickers=couple.tickers,
                        positions=user_positions
                ):
                    if roi_sum > couple.roi_stop_value and couple.check_profit \
                            or roi_sum < couple.roi_stop_value and not couple.check_profit:
                        closed_positions_count = 0
                        for symbol, position in user_positions.items():
                            if symbol in couple.tickers:
                                await self.exc_gate.close_position_by_market(tg_user_id=tg_user_id,
                                                                             position=position)
                                closed_positions_count += 1
                        if closed_positions_count > 0:
                            await self.send_realized_stops_message(couple, roi_sum)
                            self.db.remove_couple(tg_user_id=tg_user_id, couple_id=couple_id)

    async def enter_to_checking_loop(self) -> NoReturn:
        while True:
            try:
                await asyncio.sleep(5)
                await self.check_stops()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in stops checking loop: {e}")
