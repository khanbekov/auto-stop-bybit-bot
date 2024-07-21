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


class GeneralHandlers:
    router: Router = Router()

    def __init__(self, bot: Bot, dispatcher: Dispatcher, ):
        self.bot = bot
        self.dp = dispatcher
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.start_message, Command("start"))
        self.router.message.register(self.help_message, Command("help"))
        self.router.message.register(self.unknown_message)

    async def start_message(self, message: Message):
        try:
            help_message = '''
Добро пожаловать!
 
Это бот с автоматическими стопами по ROI.
    
Бот разработан <a href="https://t.me/spreadfightercis">SpreadFighter</a> для автоматического контроля позиций по ROI. 

Вам нужно создать позиции и установить ROI, по достижению которого позиция закроется.

Исходный код: <a href="https://github.com/khanbekov/auto-stop-bybit-bot">GitHub</a>
Разработчик: <a href="https://khanbekov.ru/?page_id=15">Богдан Ханбеков</a>

Получить список доступных команд: /help
'''
            await self.bot.send_message(message.from_user.id,
                                        help_message, parse_mode=ParseMode.HTML)
            await self.bot.send_message(
                message.from_user.id,
                "",
                parse_mode=ParseMode.HTML, reply_markup=main_markup
            )

        except Exception as e:
            logger.warning(f"Error on start_message() {e}", exc_info=True)

    async def help_message(self, message: Message):
        try:
            help_message = """
Доступные команды:
 <b>Управление биржей</b>
/exc &lt;название биржи&gt; - выбрать биржу для работы по умолчанию. Например, <code>/exc bybit</code>.
/exc - посмотреть какая биржа выбрана текущей
 <b>Управление стопами</b>
/new &lt;тикеры через пробел&gt; &lt;стоп ROI&gt; - создание нового стопа. Например <code>/new btc eth 4.0%</code>. Вы можете указывать любое количество тикеров, и для них будет вычисляться суммарный ROI по позициям. Для работы стопа, вы должны находиться в позициях по всем перечисленным тикерам, до этого момента он будет простаивать (таким образом, можете создать стоп заранее). Если позиции уже имеются, и указанный ROI меньше, чем текущий ROI позиций, то стоп активируется когда ROI позиций упадет. Также это работает для отрицательного ROI.
/stops - выводит список текущих стопов, включая их id, который используется в других командах.
/change &lt;id&gt; &lt;новый ROI&gt;. Например <code> /change 2 5% </code> - сменит у стопа с id 2 ROI на 5%. Если текущий ROI позиции больше, то стоп активируется, когда ROI позиции падет. Если текущее значение меньше, то когда поднимется (то есть также, как и при создании стопа). 
/remove &lt;id&gt; - удаляет стоп с заданным id.
 <b>Управление ключами</b>
/set_keys &lt;название биржи&gt; &lt;public_key&gt; &lt;private_key&gt; - Установить ключи для биржи. 
/get_keys - получить ваши ключи. Private key выводится частично в целях безопасности
/check_keys - проверить работоспособность ключей. Выводит текущий свободный баланс, по которому вы можете проверить, что ключи имеют доступ к верному аккаунту.
 <b>Прочее</b>
/positions - просмотр текущих позиций на бирже.
"""
            await self.bot.send_message(message.from_user.id,
                                        help_message, parse_mode=ParseMode.HTML)
            await self.bot.send_message(
                message.from_user.id,
                "Для начала работы выберите биржу, задайте ключи с разрешением на совершение сделок "
                "и чтение данных. После этого можете проверить текущие позиции и создать стопы.",
                parse_mode=ParseMode.HTML, reply_markup=main_markup
            )

        except Exception as e:
            logger.warning(f"Error on start_message() {e}", exc_info=True)

    async def unknown_message(self, message: Message):
        try:
            await message.reply(
                "Неизвестная команда. Вы можете использовать команду /help для инструкции по работе с ботом.",
                parse_mode=ParseMode.HTML, reply_markup=main_markup
            )

        except Exception as e:
            logger.warning(f"Error on start_message() {e}", exc_info=True)
