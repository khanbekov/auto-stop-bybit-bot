import asyncio
import logging
import time
from collections import defaultdict
from typing import NoReturn

from aiogram import Bot, Dispatcher

from src.models.position_couple import CoupleWithTickers
from src.services.exchange_gate import ExchangeGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class StopsHandler:
    activated = True

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: ExchangeGate):
        self.db = db
        self.bot = bot
        self.dp = dispatcher
        self.exc_gate = exchange_gate

    async def send_realized_stops_message(self, couple: CoupleWithTickers, current_roi: float):
        await self.bot.send_message(
            couple.tg_user_id,
            f'Закрыта позиция на {couple.exchange} по тикерам: {", ".join(couple.tickers)}.\n'
            f'Достигнут ROI {current_roi:.3f}%'
        )

    async def check_stops(self):
        all_couples = self.db.get_all_couples()
        for tg_user_id, user_couples in all_couples.items():
            couples = user_couples.values()
            exchanges = await self.get_exchanges_from_couples(couples)
            user_positions = await self.get_all_user_positions(exchanges, tg_user_id)
            for couple_id, couple in user_couples.items():
                if roi_sum := await self.exc_gate.get_roi_for_couple_with_positions(
                        tg_user_id=tg_user_id,
                        tickers=couple.tickers,
                        positions=user_positions[couple.exchange]
                ):
                    if roi_sum > couple.roi_stop_value and couple.check_profit \
                            or roi_sum < couple.roi_stop_value and not couple.check_profit:
                        closed_positions_count = 0
                        for symbol, position in user_positions[couple.exchange].items():
                            if symbol in couple.tickers:
                                await self.exc_gate.close_position_by_market(tg_user_id=tg_user_id,
                                                                             exchange=couple.exchange,
                                                                             position=position)
                                closed_positions_count += 1
                        if closed_positions_count > 0:
                            await self.send_realized_stops_message(couple, roi_sum)
                            self.db.remove_couple(tg_user_id=tg_user_id, couple_id=couple_id)

    async def get_all_user_positions(self, exchanges, tg_user_id):
        user_positions = defaultdict(dict)
        for exchange in exchanges:
            user_positions[exchange].update(self.exc_gate.get_current_positions_as_dict_on_exchange(
                tg_user_id=tg_user_id, exchange=exchange
            ))
        return user_positions

    async def get_exchanges_from_couples(self, couples):
        return list(set([couple.exchange for couple in couples]))

    def stop_checking_loop(self):
        self.activated = False

    async def enter_to_checking_loop(self) -> NoReturn:
        while self.activated:
            try:
                await asyncio.sleep(0.5)
                await self.check_stops()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in stops checking loop: {e}", exc_info=True)

