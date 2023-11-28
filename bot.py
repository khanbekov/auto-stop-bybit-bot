import asyncio
import logging
from typing import NoReturn

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import Config, load_config
from src.handlers.bybit_interaction import BybitInteraction
from src.handlers.couples_management import CouplesManagement
from src.handlers.set_api_keys import SetKeysHandler
from src.services.bybit_gate import BybitGate
from src.services.database import DBFacade
from src.services.stops_handler import StopsHandler

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
               "[%(asctime)s] - %(name)s - %(message)s",
    )

    logger.info("Starting bot")

    config: Config = load_config()

    bot: Bot = Bot(token=config.tg_bot.token, parse_mode="HTML")
    dp: Dispatcher = Dispatcher()

    db = DBFacade("sqlite:///auto_stop_bot")

    db.clear_empty_couples()

    exc = BybitGate(db.get_all_keys())

    keys_handle = SetKeysHandler(db=db, bot=bot, dispatcher=dp, exchange_gate=exc)
    exc_handle = BybitInteraction(db=db, bot=bot, dispatcher=dp, exchange_gate=exc)
    couples_management = CouplesManagement(db=db, bot=bot, dispatcher=dp, exchange_gate=exc)

    dp.include_router(keys_handle.router)
    dp.include_router(exc_handle.router)
    dp.include_router(couples_management.router)

    stops_handler = StopsHandler(db=db, bot=bot, dispatcher=dp, exchange_gate=exc)

    await setup_bot_commands(bot)

    await bot.delete_webhook(drop_pending_updates=True)

    await start(dp=dp, bot=bot, stops_handler=stops_handler)


async def start(dp: Dispatcher, bot: Bot, stops_handler: StopsHandler) -> NoReturn:
    try:
        dispatcher_task = asyncio.create_task(dp.start_polling(bot))
        stops_checking_task = asyncio.create_task(stops_handler.enter_to_checking_loop())

        await asyncio.gather(
            dispatcher_task,
            stops_checking_task,
        )

    finally:
        await dp.storage.close()
        await bot.close()


async def setup_bot_commands(bot: Bot) -> None:
    """
    Set up the available bot commands.

    :return: None
    """
    bot_commands = [
        BotCommand(command="/start", description="Приветствие"),
        BotCommand(command="/help", description="Инструкция по работе с ботом"),
        BotCommand(command="/set_keys", description="Установить новые ключи. /set_keys <public_key> <private_key>"),
        BotCommand(command="/get_keys", description="Получить ваши ключи. Private key выводится частично в целях "
                                                    "безопасности"),
        BotCommand(command="/check_keys", description="Проверить, можно ли с помощью ключей подключиться к бирже."),
        BotCommand(command="/positions", description="Получить все текущие позиции."),
        BotCommand(command="/new", description="Создать новый стоп. "
                                               "Использование /new <тикеры, разделенные пробелом> "
                                               "<стоп ROI в процентах>"),
        BotCommand(command="/stops", description="Получить все текущие стопы."),
        BotCommand(command="/remove", description="Удалить стоп. Использование /remove <id>"),
        BotCommand(command="/change", description="Изменить стоп. Использование /change <id>"
                                                  " <новый стоп ROI в процентах>"),
    ]
    await bot.set_my_commands(bot_commands)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
