import requests
import logging
import aiohttp
import asyncio
import json
from config import SUPPLY_WB_API_KEY, TARGET_WAREHOUSE_ID, ANALYTICS_WB_API_KEY, PROMOTION_WB_API_KEY
from config import MIN_NEED_COEFFICIENT, MAX_NEED_COEFFICIENT, NEED_BOX_TYPE_ID
import uuid

class WildberriesApiService:
    """
    Класс, отвечающий за взаимодействие с API Wildberries
    """

    async def get_acceptance_coefficients(self, warehouse_ids: list = None):
        """Получение коэффициентов приёмки для складов"""
        # Если warehouse_ids пустой или None - возвращаем пустой список
        if not warehouse_ids:
            return []

        url = "https://supplies-api.wildberries.ru/api/v1/acceptance/coefficients"
        params = {'warehouseIDs': ','.join(map(str, warehouse_ids))}  # Всегда список
        headers = {
            "Authorization": f"Bearer {SUPPLY_WB_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    logging.info(f"API status: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        logging.error(f"API error: {response.status}, body: {error_text}")
                        return []

                    data = await response.json()

                    if not data:
                        logging.warning("Получен пустой ответ от API коэффициентов")
                        return []

                    formatted_data = []
                    for item in data:
                        formatted_data.append({
                            'warehouse_id': item.get('warehouseId'),
                            'warehouse_name': item.get('warehouseName'),
                            'coefficient': str(item.get('coefficient', 'N/A')),
                            'date_start': item.get('dateStart', 'N/A'),
                            'box_type_name': item.get('boxTypeName', 'Не указан'),
                            'allow_unload': item.get('allowUnload', False)
                        })

                    return formatted_data

        except aiohttp.ClientError as e:
            logging.error(f"Ошибка подключения: {str(e)}")
            return []
        except Exception as e:
            logging.exception(f"Неожиданная ошибка: {str(e)}")
            return []

    async def run_periodic_coefficients_check(self, bot, chat_id, warehouse_ids):
        TARGET_WAREHOUSE_ID = 206348
        while True:
            try:
                coefficients = await self.get_acceptance_coefficients(warehouse_ids)
                if coefficients:
                    for info in coefficients:
                        # Проверяем условия и преобразуем коэффициент в число
                        if (info['warehouse_id'] == TARGET_WAREHOUSE_ID and
                                float(info['coefficient']) <= 3.0 and
                                "Короба" in info['box_type_name']):
                            # Форматируем дату для лучшей читаемости
                            date_start = info['date_start'].replace('T', ' ').replace('Z', '')

                            message = (
                                f"Склад: {info['warehouse_name']}\n"
                                f"ID: {info['warehouse_id']}, "
                                f"Коэффициент: {info['coefficient']}, "
                                f"Дата начала: {date_start}, "
                                f"Тип поставки: {info['box_type_name']}\n"
                                "Дополнительная информация: https://seller.wildberries.ru/supplies-management/all-supplies"
                            )
                            await bot.send_message(chat_id, message)
                            logging.info(f"Отправлено сообщение: {message}")
                await asyncio.sleep(12)
            except Exception as e:
                logging.exception(f"Ошибка в периодической проверке: {str(e)}")
                await asyncio.sleep(30)




    async def check_target_warehouse_with_low_coefficients(self):
        warehouses = self.__get_warehouses()
        low_coefficient_info = []

        warehouse = next((wh for wh in warehouses if wh['ID'] == TARGET_WAREHOUSE_ID), None)

        if warehouse:
            warehouse_id = warehouse['ID']
            warehouse_name = warehouse['name']
            logging.info(f"Проверяем склад: {warehouse_name} с ID: {warehouse_id}")

            coefficients = self.__get_acceptance_coefficients(warehouse_id)

            for coefficient_info in coefficients:
                coefficient = coefficient_info.get("coefficient", 0)
                box_type_id = coefficient_info.get("boxTypeID", None)
                box_type_name = coefficient_info.get("boxTypeName", "")

                if (MAX_NEED_COEFFICIENT >= coefficient >= MIN_NEED_COEFFICIENT) and (
                        box_type_id == NEED_BOX_TYPE_ID) and (
                        "QR-поставка" not in box_type_name):
                    date_start = coefficient_info.get("date", "Не указана")
                    low_coefficient_info.append({
                        "warehouse_id": warehouse_id,
                        "warehouse_name": warehouse_name,
                        "date_start": date_start,
                        "coefficient": coefficient,
                        "box_type_name": box_type_name,
                    })
                    logging.warning(f"Низкий коэффициент найден: {coefficient}")
        return low_coefficient_info
    @staticmethod
    async def get_hidden_products():
        url = 'https://seller-analytics-api.wildberries.ru/api/v1/analytics/banned-products/shadowed'
        headers = {
            'Authorization': ANALYTICS_WB_API_KEY,
        }
        params = {
            'sort': 'your_sort_value',
            'order': 'asc'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    hidden_products = data.get("data", [])
                    if hidden_products:
                        message = "Список скрытых товаров:\n"
                        for product in hidden_products:
                            message += f"ID: {product.get('id')}, Название: {product.get('name')}\n"
                        return message
                    else:
                        return "Скрытых товаров не найдено."
                else:
                    error_message = await response.text()
                    logging.error(f"Ошибка при получении данных: {response.status}, {error_message}")
                    return f"Ошибка при получении данных: {response.status}, {error_message}"

    @staticmethod
    def __get_warehouses():
        url = "https://supplies-api.wildberries.ru/api/v1/warehouses"
        headers = {
            'Authorization': f'Bearer {SUPPLY_WB_API_KEY}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error("Ошибка при получении списка складов:")
            return []

    @staticmethod
    def __get_acceptance_coefficients(warehouse_id):
        url = f"https://supplies-api.wildberries.ru/api/v1/acceptance/coefficients?warehouseIDs={warehouse_id}"
        headers = {
            'Authorization': f'Bearer {SUPPLY_WB_API_KEY}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Ошибка при получении коэффициентов для склада {warehouse_id}: {response.status_code}")
            return []

    async def getting_product_search_queries(self):
        headers = {
            'Authorization': f'Bearer {ANALYTICS_WB_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            "currentPeriod": {
                "startDate": "2025-03-01",
                "endDate": "2025-03-27"
            },
            "pastPeriod": {
                "startDate": "2025-02-01",
                "endDate": "2024-02-27"},
            "nmIds": [310364796],
            "topOrderBy": "openToCart",
            "orderBy": {
                "field": "avgPosition",
                "mode": "asc"
            },
            "limit": 20
        }

        url = "https://seller-analytics-api.wildberries.ru/api/v2/search-report/product/search-texts"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        return f"Неправильный запрос: {await response.text()}"
                    elif response.status == 401:
                        return "Пользователь не авторизован"
                    elif response.status == 403:
                        error_response = await response.json()
                        if 'title' in error_response and 'detail' in error_response and 'requestId' in error_response and 'origin' in error_response:
                            return f"Доступ запрещен. Заголовок ошибки: {error_response['title']}, Детали ошибки: {error_response['detail']}, Уникальный ID запроса: {error_response['requestId']}, ID внутреннего сервиса WB: {error_response['origin']}"
                        else:
                            return f"Доступ запрещен: {await response.text()}"
                    elif response.status == 429:
                        return "Слишком много запросов"
                    else:
                        return f"Произошла ошибка: {response.status} - {await response.text()}"

        except Exception as e:
            logging.error(f"Ошибка при получении данных: {e}")
            return f"Ошибка при получении данных: {e}"

#Статистика по ключевым фразам
    async def get_keyword_stats(self):
        headers = {
            'Authorization': f'Bearer {PROMOTION_WB_API_KEY}'
        }
        params = {  # Параметры запроса передаются через params, а не json
            'advert_id': 132681,
            'from': '2025-03-10',
            'to': '2025-03-15'
        }
        url = 'https://advert-api.wildberries.ru/adv/v0/stats/keywords'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:  # Используем GET
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        return f"Неправильный запрос: {await response.text()}"
                    elif response.status == 401:
                        return "Пользователь не авторизован"
                    elif response.status == 403:
                        error_response = await response.json()
                        if 'title' in error_response and 'detail' in error_response and 'requestId' in error_response and 'origin' in error_response:
                            return f"Доступ запрещен. Заголовок ошибки: {error_response['title']}, Детали ошибки: {error_response['detail']}, Уникальный ID запроса: {error_response['requestId']}, ID внутреннего сервиса WB: {error_response['origin']}"
                        else:
                            return f"Доступ запрещен: {await response.text()}"
                    elif response.status == 429:
                        return "Слишком много запросов"
                    else:
                        return f"Произошла ошибка: {response.status} - {await response.text()}"
        except Exception as e:
            logging.error(f"Ошибка при получении данных: {e}")
            return f"Ошибка при получении данных: {e}"

#Статистика карточек товаров за период
    async def get_sales_funnel(self):
        headers = {
            'Authorization': f'Bearer {ANALYTICS_WB_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            'brandNames': [],
            'objectIDs': [],
            'tagIDs': [],
            'nmIDs': [310364796],
            'timezone': '',
            'period': {
                'begin': '2025-03-01 00:00:00',
                'end': '2025-03-10 23:59:59'
            },
            'orderBy': {
                'field': 'openCard',
                'mode': 'asc'
            },
            'page': 1
        }

        url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/detail'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        return f"Неправильный запрос: {await response.text()}"
                    elif response.status == 401:
                        return "Пользователь не авторизован"
                    elif response.status == 403:
                        return "Доступ запрещен"
                    elif response.status == 429:
                        return "Слишком много запросов"
                    else:
                        return f"Произошла ошибка: {response.status} - {await response.text()}"

        except Exception as e:
            logging.error(f"Ошибка при получении данных: {e}")
            return f"Ошибка при получении данных: {e}"
    async def create_report(self):
        headers = {
            'Authorization': f'Bearer {ANALYTICS_WB_API_KEY}',
            'Content-Type': 'application/json'
        }
        report_id = str(uuid.uuid4())
        data = {
            'id': report_id,
            'reportType': 'DETAIL_HISTORY_REPORT',
            'userReportName': 'My_First_Report',

            'params': {
                'nmIDs': [310364796],
                'subjectIds': [],
                'brandNames': [],
                'tagIds': [],
                'startDate': '2025-03-01',
                'endDate': '2025-03-27',
                'timezone': 'Europe/Moscow',
                'aggregationLevel': 'day',
                'skipDeletedNm': False
            }
        }

        url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/downloads'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        return f"Неправильный запрос: {await response.text()}"
                    elif response.status == 401:
                        return "Пользователь не авторизован"
                    elif response.status == 403:
                        return "Доступ запрещен"
                    elif response.status == 429:
                        return "Слишком много запросов"
                    else:
                        return f"Произошла ошибка: {response.status} - {await response.text()}"

        except Exception as e:
            logging.error(f"Ошибка при получении данных: {e}")
            return f"Ошибка при получении данных: {e}"

    async def get_adverts(self):
        url = "https://advert-api.wildberries.ru/adv/v0/adverts"
        headers = {
            "Authorization": f"Bearer {PROMOTION_WB_API_KEY}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        adverts = await response.json() or []  # Если API вернул None, делаем пустой список

                        if not adverts:  # Проверяем, есть ли кампании
                            return "У вас нет активных рекламных кампаний."

                        # Формируем строку со списком кампаний
                        adverts_list = "\n".join(f"📢 {adv['name']} (ID: {adv['id']})" for adv in adverts)
                        return f"Кампании:\n{adverts_list}"

                    else:
                        return f"Ошибка {response.status}: {await response.text()}"
        except Exception as e:
            return f"Ошибка: {e}"