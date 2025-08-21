import logging
import pprint
from typing import Any
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup
import re
from config import TELEGRAM_TOKEN1, SUPPLY_WB_API_KEY
from services import WildberriesApiService
import asyncio
book_slot_command = "bookslot"
from slot_browser_booker import book_slot_via_browser

activate_monitoring_command = "activate_monitoring"
get_acceptance_coefficients = "get_acceptance_coefficients"
check_target_warehouse_with_low_coefficients = "check_target_warehouse_with_low_coefficients"
check_hidden_products_command = "check_hidden_products"
start_command = "start"
getting_product_search_queries_command = "getting_product_search_queries"
getting_keyword_statistics = "getting_keyword_statistics"
get_sales_funnel = "get_sales_funnel"
create_report = "create_report"
get_adverts = "get_adverts"


class TelegramRequestsHandler:
    """
    Класс, отвечающий за ответы телеграмм бота на комманды пользователя
    """

    def __init__(self, wildberries_api_service: WildberriesApiService):
        self.wildberries_api_service = wildberries_api_service

        self.bot = Bot(token=TELEGRAM_TOKEN1)
        self.dp = Dispatcher()
        self.active_monitoring_tasks = {}

        keyboard_buttons = [
            [
                types.KeyboardButton(text="/" + activate_monitoring_command),
                types.KeyboardButton(text="/" + get_acceptance_coefficients),
                types.KeyboardButton(text="/" + check_target_warehouse_with_low_coefficients),
                types.KeyboardButton(text="/" + check_hidden_products_command),
                types.KeyboardButton(text="/" + getting_product_search_queries_command),
                types.KeyboardButton(text="/" + getting_keyword_statistics),
                types.KeyboardButton(text="/" + get_sales_funnel),
                types.KeyboardButton(text="/" + create_report),
                types.KeyboardButton(text="/" + get_adverts),
                types.KeyboardButton(text="/" + book_slot_command)
            ],
        ]
        self.reply_keyboard = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)

        self.dp.message.register(self.__handle_start, (Command(start_command)))
        self.dp.message.register(self.__handle_activate_monitoring, (Command(activate_monitoring_command)))
        self.dp.message.register(self.__handle_get_acceptance_coefficients, (Command(get_acceptance_coefficients)))
        self.dp.message.register(self.__handle_activate_monitoring, (Command(check_target_warehouse_with_low_coefficients)))
        self.dp.message.register(self.__handle_check_hidden_products, (Command(check_hidden_products_command)))
        self.dp.message.register(self.__handle_getting_product_search_queries, (Command(getting_product_search_queries_command)))
        self.dp.message.register(self.__handle_check_get_keyword_stats, (Command(getting_keyword_statistics)))
        self.dp.message.register(self.__handler_get_sales_funnel, (Command(get_sales_funnel)))
        self.dp.message.register(self.__handler_create_report, (Command(create_report)))
        self.dp.message.register(self.__handler_get_adverts, (Command(get_adverts)))
        self.dp.message.register(self.__handle_book_slot, (Command(book_slot_command)))

    async def start_handling(self):
        await self.dp.start_polling(self.bot, handle_signals=False)

    async def __handle_start(self, message: types.Message):
        logging.warning(message.chat.id)
        await message.answer("Привет, это бот", reply_markup=self.reply_keyboard)

    async def __handle_activate_monitoring(self, message: types.Message):
        await message.answer("Отслеживание складов: ")
        response_message = await self.wildberries_api_service.check_target_warehouse_with_low_coefficients()
        await message.answer(response_message, reply_markup=self.reply_keyboard)

    async def __handle_get_acceptance_coefficients(self, message: types.Message):
        chat_id = message.chat.id

        # Останавливаем предыдущий мониторинг, если был
        if chat_id in self.active_monitoring_tasks:
            try:
                self.active_monitoring_tasks[chat_id].cancel()
                await asyncio.sleep(1)  # Даем задаче время на завершение
            except:
                pass
            del self.active_monitoring_tasks[chat_id]

        # Обновленное сообщение с информацией о двух складах
        await message.answer(
            "✅ Запущен мониторинг складов:\n"
            "• Тула (ID 206348)\n"
            "• Подольск (ID 158311)\n\n"
            "• Будут приходить уведомления при коэффициенте ≤ 3 на любом из складов\n"
            "• Только для поставок типа 'Короба'\n"
            "• Обновление каждые 12 секунд"
        )

        # ID складов для мониторинга (оба склада)
        TARGET_WAREHOUSE_IDS = [206348, 158311]

        # Запускаем мониторинг
        task = asyncio.create_task(
            self.wildberries_api_service.run_periodic_coefficients_check(
                bot=self.bot,
                chat_id=chat_id,
                warehouse_ids=TARGET_WAREHOUSE_IDS
            )
        )
        self.active_monitoring_tasks[chat_id] = task

        # Добавляем обработчик завершения задачи
        def cleanup_callback(fut):
            try:
                if chat_id in self.active_monitoring_tasks:
                    del self.active_monitoring_tasks[chat_id]
            except:
                pass

        task.add_done_callback(cleanup_callback)

        # Добавляем обработчик завершения задачи
        def cleanup_callback(fut):
            try:
                if chat_id in self.active_monitoring_tasks:
                    del self.active_monitoring_tasks[chat_id]
            except:
                pass

        task.add_done_callback(cleanup_callback)


    async def __handle_check_hidden_products(self, message: types.Message):
        await message.answer("Ваши скрытые карточки: ")
        response_message = await self.wildberries_api_service.get_hidden_products()
        await message.answer(response_message, reply_markup=self.reply_keyboard)

    async def __handle_getting_product_search_queries(self, message: types.Message):
        await message.answer("Поисковые запросы: ")
        response_message = await self.wildberries_api_service.getting_product_search_queries()
        await message.answer(response_message, reply_markup=self.reply_keyboard)

    async def __handle_check_get_keyword_stats(self, message: types.Message):
        await message.answer("Статистика по ключевым фразам: ")
        response_message = await self.wildberries_api_service.get_keyword_stats()
        await message.answer(response_message, reply_markup=self.reply_keyboard)

    async def __handler_get_sales_funnel(self, message: Any):
        await message.answer("Получаю воронку продаж... Пожалуйста, подождите.")

        try:
            response_message = await self.wildberries_api_service.get_sales_funnel()

            if response_message is None:
                await message.answer("Данные по воронке продаж не найдены.")
                return

            key_translation = {
                "brandNames": "Бренды",
                "objectIDs": "ID предметов",
                "tagIDs": "ID ярлыков",
                "nmIDs": "Артикулы Wildberries",
                "timezone": "Временная зона",
                "period": "Период",
                "orderBy": "Сортировка",
                "page": "Страница",
                "openCardCount": "Переходы в карточку товара",
                "addToCart": "Добавления в корзину",
                "orders": "Количество заказов",
                "avgRubPrice": "Средняя цена (₽)",
                "ordersSumRub": "Сумма заказов (₽)",
                "stockMpQty": "Остатки на маркетплейсе (шт.)",
                "stockWbQty": "Остатки на складе (шт.)",
                "cancelSumRub": "Сумма возвратов (₽)",
                "cancelCount": "Количество возвратов",
                "buyoutCount": "Количество выкупов",
                "buyoutSumRub": "Сумма выкупов (₽)",
                "brandName": "Название бренда",
                "nmID": "Артикул",
                "vendorCode": "Артикул поставщика",
            }

            def translate_keys(data):
                if isinstance(data, dict):
                    return {key_translation.get(k, k): translate_keys(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [translate_keys(item) for item in data]
                else:
                    return data

            def escape_markdown_v2(text):
                """
                Экранирует специальные символы для Telegram MarkdownV2.
                """
                return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

            translated_data = translate_keys(response_message)
            details = f"```\n{pprint.pformat(translated_data, width=80)}\n```"

            # Экранирование специальных символов
            details = escape_markdown_v2(details)

            # Отправка длинного сообщения частями
            if len(details) > 4000:
                chunks = [details[i:i + 4000] for i in range(0, len(details), 4000)]
                for chunk in chunks:
                    await message.answer(chunk, parse_mode="MarkdownV2")
            else:
                await message.answer(details, parse_mode="MarkdownV2")

        except Exception as e:
            await message.answer(f"Произошла ошибка: {str(e)}")

    async def __handler_create_report(self, message: types.Message):
        await message.answer("Создание отчета: ")
        response_message = await self.wildberries_api_service.create_report()
        await message.answer(response_message, reply_markup=self.reply_keyboard)

    async def __handler_get_adverts(self, message: types.Message):
        await message.answer("Кампании: ")
        response_message = await self.wildberries_api_service.get_adverts()
        await message.answer(response_message, reply_markup=self.reply_keyboard)

    async def __handle_book_slot(self, message: types.Message):
        await message.answer("🔄 Запускаю попытки брони слота...")

        async def try_loop():
            while True:
                success = book_slot_via_browser("cookies.txt")
                if success:
                    await message.answer("✅ Слот успешно забронирован!")
                    break
                await asyncio.sleep(10)  # интервал между попытками

        asyncio.create_task(try_loop())

#####################СЛОВАРЬ
'''key_translation = {
                    "brandNames": "Бренды",
                    "objectIDs": "ID предметов",
                    "tagIDs": "ID ярлыков",
                    "nmIDs": "Артикулы Wildberries",
                    "timezone": "Временная зона",
                    "period": "Период",
                    "orderBy": "Сортировка",
                    "page": "Страница",
                    "openCardCount": "Переходы в карточку товара",
                    "addToCart": "Добавления в корзину",
                    "orders": "Количество заказов",
                    "avgRubPrice": "Средняя цена (₽)",
                    "ordersSumRub": "Сумма заказов (₽)",
                    "stockMpQty": "Остатки на маркетплейсе (шт.)",
                    "stockWbQty": "Остатки на складе (шт.)",
                    "cancelSumRub": "Сумма возвратов (₽)",
                    "cancelCount": "Количество возвратов",
                    "buyoutCount": "Количество выкупов",
                    "buyoutSumRub": "Сумма выкупов (₽)",
                    "brandName": "Название бренда",
                    "nmID": "Артикул",
                    "periodComparasion": "Период",
                    "additionalErrors": "Дополнительные ошибки",
                    "brandNames": "Названия брендов",
                    "objectIDs": "ID объектов",
                    "tagIDs": "ID тегов",
                    "nmIDs": "Артикулы Wildberries",
                    "timezone": "Часовой пояс",
                    "period": "Период",
                    "orderBy": "Сортировка",
                    "page": "Страница",
                    "openCard": "Переходы в карточку товара",
                    "addToCart": "Добавления в корзину",
                    "orders": "Количество заказов",
                    "avgRubPrice": "Средняя цена (₽)",
                    "ordersSumRub": "Сумма заказов (₽)",
                    "stockMpQty": "Остатки на маркетплейсе (шт.)",
                    "stockWbQty": "Остатки на складе (шт.)",
                    "cancelSumRub": "Сумма возвратов (₽)",
                    "cancelCount": "Количество возвратов",
                    "buyoutCount": "Количество выкупов",
                    "buyoutSumRub": "Сумма выкупов (₽)",
                    "brandName": "Название бренда",
                    "nmID": "Артикул",
                    "periodComparasion": "Сравнение периодов",
                    "isNextPage": "Есть ли следующая страница",
                    "Страница": "Страница",
                    "Сумма возвратов (₽)": "Сумма возвратов (₽)",
                    "Сумма заказов (₽)": "Сумма заказов (₽)",
                    "Количество возвратов": "Количество возвратов",
                    "Количество заказов": "Количество заказов",
                    "Конверсии": "Конверсии",
                    "Динамика": "Динамика",
                    "previousPeriod": "Предыдущий период",
                    "selectedPeriod": "Выбранный период",
                    "begin": "Начало",
                    "end": "Конец",
                    "avgOrdersCountPerDay": "Среднее количество заказов в день",
                    "avgPriceRub": "Средняя цена (₽)",
                    "addToCartCount": "Добавления в корзину",
                    "openCard": "Переходы в карточку товара",
                    "ordersCount": "Количество заказов",
                    "ordersSumRub": "Сумма заказов (₽)",
                    "stockMp": "Остатки на маркетплейсе",
                    "stockWb": "Остатки на складе",
                    "buyoutsCount": "Количество выкупов",
                    "buyoutsSumRub": "Сумма выкупов (₽)",
                    "cancelCount": "Количество возвратов",
                    "cancelSumRub": "Сумма возвратов (₽)",
                    "conversions": "Конверсии",
                    "addToCartPercent": "Добавления в корзину (%)",
                    "buyoutsPercent": "Выкупы (%)",
                    "cartToOrderPercent": "Конверсия из корзины в заказ (%)",
                    "addToCartDynamics": "Динамика добавлений в корзину",
                    "avgOrdersCountPerDayDynamics": "Динамика среднего количества заказов в день",
                    "avgPriceRubDynamics": "Динамика средней цены (₽)",
                    "buyoutsCountDynamics": "Динамика выкупов",
                    "buyoutsSumRubDynamics": "Динамика суммы выкупов (₽)",
                    "cancelCountDynamics": "Динамика количества возвратов",
                    "cancelSumRubDynamics": "Динамика суммы возвратов (₽)",
                    "conversions": "Конверсии",
                    "openCardDynamics": "Динамика переходов в карточку товара",
                    "ordersCountDynamics": "Динамика количества заказов",
                    "ordersSumRubDynamics": "Динамика суммы заказов (₽)",
                    "stockMpQty": "Остатки на маркетплейсе (шт.)",
                    "stockWbQty": "Остатки на складе (шт.)",
                    "vendorCode": "Артикул поставщика",
                    } '''
