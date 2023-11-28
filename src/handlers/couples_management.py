import logging

from aiogram import Router, Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command

from src.services.bybit_gate import BybitGate
from src.services.database import DBFacade

logger = logging.getLogger(__name__)


class CouplesManagement:
    router: Router = Router()

    def __init__(self, db: DBFacade, bot: Bot, dispatcher: Dispatcher, exchange_gate: BybitGate):
        self.db = db
        self.bot = bot
        self.dp = dispatcher
        self.exc_gate = exchange_gate
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.start_message, Command("start"))
        self.router.message.register(self.start_message, Command("help"))
        self.router.message.register(self.create_new_couple, Command("new"))
        self.router.message.register(self.get_couples, Command("stops"))
        self.router.message.register(self.remove_couple, Command("remove"))
        self.router.message.register(self.change_couple_roi_stop_value, Command("change"))

    async def start_message(self, message: Message):
        try:
            help_message = """
Добро пожаловать в бота с автоматическими стопами по ROI!
Доступные команды:
        -- управление стопами --
 /new &lt;тикеры через пробел&gt; &lt;стоп ROI&gt; - создание нового стопа. Например <code>/new BTC/USDT:USDT ETH/USDT:USDT 4.0%</code>. Вы можете указывать любое количество тикеров, и для них будет вычисляться суммарный ROI по позициям. Для работы стопа, вы должны находиться в позициях по всем перечисленным тикерам, до этого момента он будет простаивать (таким образом, можете создать стоп заранее). Если позиции уже имеются, и указанный ROI меньше, чем текущий ROI позиций, то стоп активируется когда ROI позиций упадет. Также это работает для отрицательного ROI.
 /stops - выводит список текущих стопов, включая их id, который используется в других командах.
 /change &lt;id&gt; &lt;новый ROI&gt;. Например <code> /change 2 5% </code> - сменит у стопа с id 2 ROI на 5%. Если текущий ROI позиции больше, то стоп активируется, когда ROI позиции падет. Если текущее значение меньше, то когда поднимется (то есть также, как и при создании стопа). 
 /remove &lt;id&gt; - удаляет стоп с заданным id.
        -- управление ключами --
 /set_keys &lt;public_key&gt; &lt;private_key&gt; - Установить новые ключи. 
 /get_keys - получить ваши ключи. Private key выводится частично в целях безопасности
 /check_keys - проверить работоспособность ключей. Выводит текущий свободный баланс, по которому вы можете проверить, что ключи имеют доступ к верному аккаунту.
        --- прочее --
 /positions - просмотр текущих позиций на бирже.
"""
            await self.bot.send_message(message.from_user.id,
                                        help_message, parse_mode=ParseMode.HTML)
            await self.bot.send_message(
                message.from_user.id,
                "Для начала работы задайте ключи от биржи, с разрешением на совершение сделок "
                "и чтение данных. После этого можете проверить текущие позиции и создать стопы.",
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            logger.warning(f"Error on start_message() {e}", exc_info=True)

    async def create_new_couple(self, message: Message):
        try:
            tickers = message.text.split()[1:-1]
            roi_stop_value = float(message.text.split()[-1].strip().replace('%', ''))

            current_roi = await self.exc_gate.get_sum_roi_for_couple(message.from_user.id, tickers)
            self.db.add_couple(
                tg_user_id=message.from_user.id,
                tickers=tickers,
                roi_stop_value=roi_stop_value,
                check_profit=roi_stop_value > current_roi
            )
            await message.reply(text=f"Добавлен стоп [{', '.join(tickers)}], c ROI {roi_stop_value}%.")
        except Exception as e:
            await message.reply(text="Не удалось добавить стоп, попробуйте ещё раз.")
            logger.warning(f"Error on create_new_couple() {e}", exc_info=True)

    async def get_couples(self, message: Message):
        try:
            couples = self.db.get_user_couples(message.from_user.id)

            answer = 'Id : Tickers : Stop ROI\n' \
                     '-----------------------------'
            for key, couple in couples.items():
                answer += f'\n{key}   :   {", ".join(couple.tickers)}  :  {couple.roi_stop_value}%'

            await message.reply(text=f"Текущие стопы:\n\n{answer}")
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

            await message.reply(text=f"Удален стоп:\n\n{answer}")
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

            current_roi = await self.exc_gate.get_sum_roi_for_couple(message.from_user.id, couple.tickers)
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

            await message.reply(text=f"Обновлен стоп: [{', '.join(couple.tickers)}], c ROI {couple.roi_stop_value}%.")
        except Exception as e:
            await message.reply(text="Не удалось обновить стоп, попробуйте ещё раз.")
            logger.warning(f"Error on change_couple_roi_stop_value() {e}", exc_info=True)
