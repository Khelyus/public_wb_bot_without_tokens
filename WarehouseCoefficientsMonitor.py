import asyncio
import logging

from config import DELAY_BETWEEN_WAREHOUSE_COEFFICIENTS_CHECK_SEC
from services import TelegramBotService, WildberriesApiService


class WarehouseCoefficientsMonitor:
    """
    Класс, отвечающий за регулярную проверку склада
    """

    def __init__(self, telegram_bot_service: TelegramBotService, wildberries_api_service: WildberriesApiService):
        self.telegram_bot_service = telegram_bot_service
        self.wildberries_api_service = wildberries_api_service

    async def start_monitoring(self):
        TARGET_WAREHOUSE_ID = 206348
        logging.info("Начало главного цикла программы")
        while True:
            # Получаем коэффициенты приёмки
            acceptance_coefficients_info = await self.wildberries_api_service.get_acceptance_coefficients()

            if acceptance_coefficients_info:
                for info in acceptance_coefficients_info:
                    # Фильтруем по условиям
                    if (info['warehouse_id'] == TARGET_WAREHOUSE_ID and
                            info['coefficient'] <= 3 and
                            info['box_type_name'] == "Короба"):
                        message = (
                            f"Склад: {info['warehouse_name']}\n"
                            f"Коэффициент приёмки: {info['coefficient']}, "
                            f"Тип поставки: {info['box_type_name']}\n"
                            "Дополнительная информация: https://seller.wildberries.ru/supplies-management/all-supplies"
                        )
                        logging.info(message)
                        await self.telegram_bot_service.send_message(message)

            # Получаем информацию о складах с низким коэффициентом
            low_coefficient_info = await self.wildberries_api_service.check_target_warehouse_with_low_coefficients()

            if low_coefficient_info:
                for info in low_coefficient_info:
                    # Фильтруем по условиям
                    if (info['warehouse_id'] == TARGET_WAREHOUSE_ID and
                            info['coefficient'] <= 3 and
                            info['box_type_name'] == "Короба"):
                        message = (
                            f"Склад: {info['warehouse_name']}\n"
                            f"ID: {info['warehouse_id']}, "
                            f"Коэффициент: {info['coefficient']}, "
                            f"Дата начала: {info['date_start']}, "
                            f"Тип поставки: {info['box_type_name']}\n"
                            "Дополнительная информация: https://seller.wildberries.ru/supplies-management/all-supplies"
                        )
                        logging.info(message)
                        await self.telegram_bot_service.send_message(message)

            await asyncio.sleep(DELAY_BETWEEN_WAREHOUSE_COEFFICIENTS_CHECK_SEC)
