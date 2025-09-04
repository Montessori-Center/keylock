# services/dataforseo_client.py
import requests
import base64
from typing import List, Dict, Any, Optional
from config import Config

class DataForSeoClient:
    """Клиент для работы с DataForSeo API"""
    
    BASE_URL = "https://api.dataforseo.com/v3"
    
    def __init__(self, login: str = None, password: str = None):
        self.login = login or Config.DATAFORSEO_LOGIN
        self.password = password or Config.DATAFORSEO_PASSWORD
        self.auth_string = base64.b64encode(
            f"{self.login}:{self.password}".encode()
        ).decode()
    
    def _make_request(self, method: str, endpoint: str, data: Any = None) -> Dict:
        """Базовый метод для выполнения запросов к API"""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Basic {self.auth_string}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to DataForSeo: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
    
    def get_keywords_for_keywords(
        self,
        keywords: List[str],
        location_code: int = 2804,  # Ukraine
        language_code: str = "ru",
        search_partners: bool = False,
        sort_by: str = "search_volume",
        limit: int = 700,
        include_seed_keyword: bool = True,
        include_clickstream_data: bool = False,
        include_serp_info: bool = True  # Включаем информацию о SERP
    ) -> Dict:
        """
        Получение списка ключевых слов по seed keywords (LIVE режим)
        Документация: https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/
        
        Args:
            keywords: Список исходных ключевых слов (макс. 1000)
            location_code: Код локации (2804 для Украины)
            language_code: Код языка
            search_partners: Включать ли партнеров поиска
            sort_by: Поле для сортировки результатов
            limit: Максимальное количество результатов (макс. 700 для live)
            include_seed_keyword: Включать ли исходные ключевые слова в результаты
            include_clickstream_data: Включать ли данные Clickstream
            include_serp_info: Включать ли информацию о SERP
        """
        
        endpoint = "/keywords_data/google_ads/keywords_for_keywords/live"
        
        # Структура запроса по документации
        data = [{
            "keywords": keywords[:1000],  # Ограничение API - макс 1000 ключевых слов
            "location_code": location_code,
            "language_code": language_code,
            "search_partners": search_partners,
            "sort_by": sort_by,
            "limit": limit,
            "include_seed_keyword": include_seed_keyword,
            "include_clickstream_data": include_clickstream_data,
            "include_serp_info": include_serp_info,
            "date_from": "2024-01-01",  # Для получения исторических данных
        }]
        
        return self._make_request("POST", endpoint, data)
    
    def parse_keywords_response(self, response: Dict) -> List[Dict]:
        """
        Парсинг ответа с ключевыми словами
        
        Returns:
            Список словарей с данными ключевых слов
        """
        keywords_data = []
        
        if not response.get("tasks"):
            print("No tasks in response")
            return keywords_data
        
        # Проходим по всем задачам
        for task in response.get("tasks", []):
            if task.get("status_code") != 20000:
                print(f"Task error: {task.get('status_message')}")
                continue
            
            # Получаем результаты из задачи
            if not task.get("result"):
                continue
                
            for result_item in task.get("result", []):
                items = result_item.get("items", [])
                
                for item in items:
                    # Извлекаем данные ключевого слова
                    keyword_data = item.get("keyword_data", {})
                    keyword_info = keyword_data.get("keyword_info", {})
                    serp_info = keyword_data.get("serp_info", {})
                    impressions_info = keyword_data.get("impressions_info", {})
                    
                    # Вычисляем изменения
                    monthly_searches = keyword_info.get("monthly_searches", [])
                    three_month_change = None
                    yearly_change = None
                    
                    if monthly_searches and len(monthly_searches) >= 3:
                        # Изменение за 3 месяца
                        current = monthly_searches[-1].get("search_volume", 0)
                        three_months_ago = monthly_searches[-3].get("search_volume", 0)
                        if three_months_ago > 0:
                            three_month_change = ((current - three_months_ago) / three_months_ago) * 100
                    
                    if monthly_searches and len(monthly_searches) >= 12:
                        # Изменение за год
                        current = monthly_searches[-1].get("search_volume", 0)
                        year_ago = monthly_searches[-12].get("search_volume", 0)
                        if year_ago > 0:
                            yearly_change = ((current - year_ago) / year_ago) * 100
                    
                    # Определяем тип конкуренции
                    competition_level = keyword_info.get("competition", "UNSPECIFIED")
                    competition_map = {
                        "HIGH": "Высокая",
                        "MEDIUM": "Средняя",
                        "LOW": "Низкая",
                        "UNSPECIFIED": "Неизвестно"
                    }
                    
                    keywords_data.append({
                        "keyword": keyword_data.get("keyword", ""),
                        "avg_monthly_searches": keyword_info.get("search_volume", 0),
                        "competition": competition_map.get(competition_level, competition_level),
                        "competition_percent": keyword_info.get("competition_index", 0),
                        "min_top_of_page_bid": keyword_info.get("low_top_of_page_bid", 0),
                        "max_top_of_page_bid": keyword_info.get("high_top_of_page_bid", 0),
                        "three_month_change": round(three_month_change, 2) if three_month_change else None,
                        "yearly_change": round(yearly_change, 2) if yearly_change else None,
                        
                        # Дополнительная информация из SERP
                        "serp_item_types": serp_info.get("serp_item_types", []),
                        "se_results_count": serp_info.get("se_results_count", 0),
                        
                        # CPC из impressions_info
                        "cpc": impressions_info.get("cpc_max", keyword_info.get("cpc", 0)),
                        
                        # Дополнительные метрики
                        "keyword_difficulty": keyword_data.get("keyword_properties", {}).get("keyword_difficulty", None)
                    })
        
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
        endpoint = "/appendix/user_data"
        return self._make_request("GET", endpoint)

# Создаем глобальный экземпляр клиента
dataforseo_client = DataForSeoClient()