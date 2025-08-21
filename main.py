import logging
import asyncio

from config import AFTER_ERROR_RESTART_DELAY_SEC
from modules.logger_module import initialize_logger
from TelegramRequestsHandler import TelegramRequestsHandler
from WarehouseCoefficientsMonitor import WarehouseCoefficientsMonitor
from services.TelegramBotService import TelegramBotService
from services.WildberriesApiService import WildberriesApiService



async def run_all_services():
    api_service = WildberriesApiService()
    telegram_handler = TelegramRequestsHandler(api_service)

    # Запускаем только обработчик Telegram
    await telegram_handler.start_handling()



async def main():
    logging.info("Starting application")
    while True:
        try:
            await run_all_services()
        except Exception as e:
            logging.exception(f"Critical error: {str(e)}")
            await asyncio.sleep(AFTER_ERROR_RESTART_DELAY_SEC)

if __name__ == "__main__":
    initialize_logger()
    asyncio.run(main())
