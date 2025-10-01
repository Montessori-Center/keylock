# services/dataforseo_client.py - исправленная версия с правильными отступами
import requests
import base64
from typing import List, Dict, Any, Optional
from config import Config
import sys

def debug_print(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

class DataForSeoClient:
    
    BASE_URL = "https://api.dataforseo.com/v3"
    
    def __init__(self, login: str = None, password: str = None):
        debug_print(f"🔧 DataForSeoClient.__init__ вызван")
        if login and password:
            # Используем переданные явно (для тестов)
            self.login = login
            self.password = password
            debug_print(f"🔧 DataForSeo: используются переданные credentials: {login}")
        else:
            # Загружаем из настроек приложения
            try:
                from services.config_manager import config_manager
                settings = config_manager.load_settings()
                
                self.login = settings.get('dataforseo_login', '').strip()
                self.password = settings.get('dataforseo_password', '').strip()
                
                debug_print(f"📋 Логин из настроек: '{self.login}'")
                debug_print(f"📋 Пароль из настроек: {'***' if self.password else 'ПУСТОЙ'}")
                
                # Если в файле настроек пусто, пробуем переменные окружения
                if not self.login:
                    import os
                    self.login = os.environ.get('DATAFORSEO_LOGIN', '').strip()
                if not self.password:
                    import os
                    self.password = os.environ.get('DATAFORSEO_PASSWORD', '').strip()
                
                if self.login and self.password:
                    debug_print(f"✅ DataForSeo: загружены настройки из файла: {self.login}")
                else:
                    debug_print(f"⚠️ DataForSeo: настройки не найдены в файле, пробуем fallback")
                    
            except Exception as e:
                debug_print(f"❌ Ошибка загрузки DataForSeo credentials: {e}")
                # Последний fallback - переменные окружения
                import os
                self.login = os.environ.get('DATAFORSEO_LOGIN', '').strip()
                self.password = os.environ.get('DATAFORSEO_PASSWORD', '').strip()
        
        # Проверяем что credentials заполнены
        if not self.login or not self.password:
            debug_print(f"❌ Не хватает credentials:")
            debug_print(f"   - login: '{self.login}' (пустой: {not self.login})")
            debug_print(f"   - password: пустой: {not self.password}")
            raise ValueError(
                "DataForSeo API credentials are required. "
                "Set them in Settings or environment variables DATAFORSEO_LOGIN/DATAFORSEO_PASSWORD"
            )
        
        self.auth_string = base64.b64encode(
            f"{self.login}:{self.password}".encode()
        ).decode()
        
        debug_print(f"🔑 DataForSeo client initialized with login: {self.login}")
    
    def _make_request(self, method: str, endpoint: str, data: Any = None) -> Dict:
        """Базовый метод для выполнения запросов к API"""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Basic {self.auth_string}",
            "Content-Type": "application/json"
        }
        
        debug_print(f"🌐 Выполняем {method} запрос к: {url}")
        if data:
            debug_print(f"📋 Размер данных: {len(str(data))} символов")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            debug_print(f"📨 Ответ получен, статус: {response.status_code}")
            
            response.raise_for_status()
            json_response = response.json()
            debug_print(f"✅ JSON распарсен успешно")
            return json_response
        except requests.exceptions.RequestException as e:
            debug_print(f"❌ Error making request to DataForSeo: {e}")
            if hasattr(e, 'response') and e.response is not None:
                debug_print(f"❌ Response: {e.response.text}")
            raise
    
    def get_keywords_for_keywords(self,
        keywords: List[str],
        location_code: int = 2804,  # Ukraine
        language_code: str = "ru",
        search_partners: bool = False,
        sort_by: str = "search_volume",
        limit: int = 700,
        include_seed_keyword: bool = True,
        date_from: str = "2024-01-01",
        date_to: str = None
    ) -> Dict:
        
        debug_print(f"🔍 get_keywords_for_keywords вызван с параметрами:")
        debug_print(f"   - keywords: {keywords[:3]}... (всего {len(keywords)})")
        debug_print(f"   - location_code: {location_code}")
        debug_print(f"   - language_code: {language_code}")
        debug_print(f"   - limit: {limit}")
        
        endpoint = "/keywords_data/google_ads/keywords_for_keywords/live"
        
        # Структура запроса согласно официальной документации
        data = [{
            "keywords": keywords[:700],  # Ограничение API - макс 700 ключевых слов
            "location_code": location_code,
            "language_code": language_code,
            "search_partners": search_partners,
            "sort_by": sort_by,
            "limit": limit,
            "include_seed_keyword": include_seed_keyword,
            "date_from": date_from,
        }]
        
        # Добавляем date_to только если указан
        if date_to:
            data[0]["date_to"] = date_to
        
        debug_print(f"📋 Структура запроса создана")
        return self._make_request("POST", endpoint, data)
    
    def parse_keywords_response(self, response: Dict) -> List[Dict]:
        """
        Парсинг ответа с ключевыми словами (только основные данные)
        Интент и SERP данные будут определены отдельно через SERP анализ
        """
        debug_print(f"🔄 parse_keywords_response начат")
        keywords_data = []
        
        if not response.get("tasks"):
            debug_print("❌ No tasks in response")
            return keywords_data
        
        debug_print(f"📊 Количество tasks: {len(response['tasks'])}")
        
        # Проходим по всем задачам
        for task in response.get("tasks", []):
            if task.get("status_code") != 20000:
                debug_print(f"❌ Task error: {task.get('status_message')}")
                continue
            
            # Получаем результаты из задачи
            if not task.get("result"):
                debug_print("❌ No result in task")
                continue
                
            result_items = task.get("result", [])
            debug_print(f"📊 Количество result items: {len(result_items)}")
            
            # В Google Ads API каждый элемент result[] - это ключевое слово
            for keyword_item in result_items:
                debug_print(f"🔄 Обработка keyword с ключами: {list(keyword_item.keys())}")
                
                # Извлекаем основные данные
                keyword_text = keyword_item.get("keyword", "")
                search_volume = keyword_item.get("search_volume", 0)
                competition = keyword_item.get("competition", "UNSPECIFIED")
                competition_index = keyword_item.get("competition_index", 0)
                low_bid = keyword_item.get("low_top_of_page_bid", 0)
                high_bid = keyword_item.get("high_top_of_page_bid", 0)
                cpc = keyword_item.get("cpc", 0)
                monthly_searches = keyword_item.get("monthly_searches", [])
                
                debug_print(f"📝 Обрабатываем keyword: {keyword_text}")
                debug_print(f"   - search_volume: {search_volume}")
                debug_print(f"   - competition: {competition}")
                debug_print(f"   - cpc: {cpc}")
                
                # Вычисляем изменения по месяцам
                three_month_change = None
                yearly_change = None
                
                if monthly_searches and len(monthly_searches) >= 3:
                    try:
                        current = monthly_searches[-1].get("search_volume", 0)
                        three_months_ago = monthly_searches[-3].get("search_volume", 0)
                        if three_months_ago > 0:
                            three_month_change = ((current - three_months_ago) / three_months_ago) * 100
                    except (IndexError, ZeroDivisionError, TypeError):
                        debug_print("⚠️ Ошибка расчета three_month_change")
                
                if monthly_searches and len(monthly_searches) >= 12:
                    try:
                        current = monthly_searches[-1].get("search_volume", 0)
                        year_ago = monthly_searches[-12].get("search_volume", 0)
                        if year_ago > 0:
                            yearly_change = ((current - year_ago) / year_ago) * 100
                    except (IndexError, ZeroDivisionError, TypeError):
                        debug_print("⚠️ Ошибка расчета yearly_change")
                
                # Определяем тип конкуренции
                competition_map = {
                    "HIGH": "Высокая",
                    "MEDIUM": "Средняя",
                    "LOW": "Низкая",
                    "UNSPECIFIED": "Неизвестно"
                }
                
                keyword_result = {
                    "keyword": keyword_text,
                    "avg_monthly_searches": search_volume,
                    "competition": competition_map.get(competition, competition),
                    "competition_percent": competition_index,
                    "min_top_of_page_bid": low_bid,
                    "max_top_of_page_bid": high_bid,
                    "three_month_change": round(three_month_change, 2) if three_month_change else None,
                    "yearly_change": round(yearly_change, 2) if yearly_change else None,
                    "cpc": cpc,
                    # Значения по умолчанию - будут определены через SERP анализ
                    "intent_type": "Информационный",
                    "has_ads": None,
                    "has_google_maps": None,
                    "has_our_site": None,
                    "has_school_sites": None
                }
                
                keywords_data.append(keyword_result)
        
        debug_print(f"✅ Парсинг завершен: {len(keywords_data)} ключевых слов")
        if keywords_data:
            debug_print(f"📝 Первое ключевое слово: {keywords_data[0]['keyword']}")
            debug_print(f"📝 Объем поиска: {keywords_data[0]['avg_monthly_searches']}")
            debug_print(f"📝 Конкуренция: {keywords_data[0]['competition']}")
        
        return keywords_data
    
    def get_search_volume(
        self,
        keywords: List[str],
        location_code: int = 2804,
        language_code: str = "ru",
        search_partners: bool = False
    ) -> Dict:
        """
        Получение объемов поиска для списка ключевых слов
        Используется когда нужны точные объемы для конкретных ключевых слов
        """
        
        endpoint = "/keywords_data/google_ads/search_volume/live"
        
        data = [{
            "keywords": keywords[:1000],
            "location_code": location_code,
            "language_code": language_code,
            "search_partners": search_partners,
            "date_from": "2024-01-01",
            "sort_by": "search_volume"
        }]
        
        return self._make_request("POST", endpoint, data)
    
    def get_locations(self, country: str = None) -> Dict:
        """Получение списка доступных локаций"""
        endpoint = "/keywords_data/google_ads/locations"
        if country:
            endpoint += f"/{country}"
        return self._make_request("GET", endpoint)
    
    def get_languages(self) -> Dict:
        """Получение списка доступных языков"""
        endpoint = "/keywords_data/google_ads/languages"
        return self._make_request("GET", endpoint)
    
    def get_status(self) -> Dict:
        """Проверка статуса аккаунта и баланса"""
        debug_print(f"🔍 Запрос статуса аккаунта")
        endpoint = "/appendix/user_data"
        return self._make_request("GET", endpoint)
        
    def get_serp(
        self,
        keyword: str,
        location_code: int = 2804,
        language_code: str = "ru",
        device: str = "desktop",
        os: str = "windows",
        depth: int = 100,
        calculate_rectangles: bool = False,
        browser_screen_width: int = 1920,
        browser_screen_height: int = 1080,
        se_domain: str = "google.com.ua"
    ) -> Dict:
        endpoint = "/serp/google/organic/live/regular"
        
        data = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "device": device,
            "os": os,
            "depth": depth,
            "calculate_rectangles": calculate_rectangles,
            "browser_screen_width": browser_screen_width,
            "browser_screen_height": browser_screen_height,
            "se_domain": se_domain,
        }]
        
        return self._make_request("POST", endpoint, data)

# Создаем глобальный экземпляр клиента
def get_dataforseo_client(login: str = None, password: str = None) -> DataForSeoClient:
    """
    Получает экземпляр DataForSeoClient с ленивой инициализацией
    
    Args:
        login: Логин (опционально, для тестов)
        password: Пароль (опционально, для тестов)
    
    Returns:
        Экземпляр DataForSeoClient
        
    Raises:
        ValueError: Если не удалось получить credentials
    """
    debug_print(f"🔧 get_dataforseo_client вызван")
    try:
        return DataForSeoClient(login, password)
    except ValueError as e:
        debug_print(f"❌ Ошибка инициализации DataForSeo client: {e}")
        debug_print("💡 Настройте API ключи в разделе Settings")
        raise e

# Глобальная переменная для кэширования (опционально)
_cached_client = None

def get_cached_dataforseo_client() -> DataForSeoClient:
    """Получает кэшированный экземпляр клиента"""
    global _cached_client
    if _cached_client is None:
        _cached_client = get_dataforseo_client()
    return _cached_client

def clear_client_cache():
    """Очищает кэш клиента (для обновления настроек)"""
    global _cached_client
    _cached_client = None