import os
import asyncio
import aiohttp
import random
from dotenv import load_dotenv
import json
from typing import List, Dict, Any, AsyncGenerator, Tuple, Optional, Type, TypeVar
from tqdm.asyncio import tqdm
from aiolimiter import AsyncLimiter
from pydantic import BaseModel, ValidationError

from scripts.logger import logger
from scripts.config import URL_JSON_PATH
from scripts.schemas import UserBase, MatchResponse, TopRankerResponse

# .env 파일에서 환경 변수 로드
load_dotenv()

# URL 로드
with open(URL_JSON_PATH) as f:
    URLS = json.load(f)

BASE_URL = URLS['base_url']

T = TypeVar('T', bound=BaseModel) # Pydantic 모델 타입 변수

# 전역 Rate Limiter 설정 (초당 50 요청)
GLOBAL_LIMITER = AsyncLimiter(50, 1)

class ERAPIClient:
    def __init__(self, api_key: Optional[str] = None): # API Key를 인자로 받거나 환경 변수에서 로드
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API Key is missing. Set API_KEY env var or pass it to constructor.")
        
        self.headers = {
            "accept": "application/json",
            "x-api-key": self.api_key
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.limiter = GLOBAL_LIMITER

    async def __aenter__(self):
        """ 비동기 컨텍스트 매니저 진입 시 세션 생성 """
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """ 비동기 컨텍스트 매니저 종료 시 세션 종료 """
        if self.session:
            await self.session.close()

    async def _fetch_json(
        self,
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        response_model: Optional[Type[T]] = None
    ) -> Any | T | None:
        """재시도 로직과 Rate Limiting을 포함하여 JSON을 가져오는 내부 메서드.

        지수 백오프(Exponential Backoff)와 전역 Rate Limiter를 적용하여
        API 호출 제한(429)과 네트워크 오류에 안전하게 대응합니다.

        Args:
            url: 요청할 API 엔드포인트 URL.
            params: URL 쿼리 파라미터 딕셔너리.
            max_retries: 최대 재시도 횟수 (기본값: 5).
            initial_delay: 첫 재시도 대기 시간(초) (기본값: 1.0).
            response_model: 응답 검증에 사용할 Pydantic 모델 클래스.

        Returns:
            성공 시 JSON 딕셔너리 또는 Pydantic 모델 인스턴스.
            실패 시 None.

        Raises:
            RuntimeError: 세션이 초기화되지 않은 경우.
        """
        if not self.session: # 세션이 초기화되지 않은 경우
            raise RuntimeError("Client session is not initialized. Use 'async with ERAPIClient() as client:'.")

        for attempt in range(max_retries): # 재시도 루프
            try:
                async with self.limiter:
                    pass

                async with self.session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        raw_data = await response.json()
                        
                        # 1. Pydantic Validation
                        if response_model:
                            try:
                                validated_data = response_model.parse_obj(raw_data)
                                return validated_data
                            except ValidationError as ve:
                                logger.error(f"Validation error for url {url}: {ve}")
                                return None
                        
                        # 2. Basic Validation
                        if raw_data.get("code") == 200:
                            return raw_data
                        elif raw_data.get("code") == 429:
                            logger.warning(f"API Rate limit (429 internal) hit for url: {url}. Retrying...")
                        else:
                            logger.error(f"API internal error - url: {url}, code: {raw_data.get('code')}, message: {raw_data.get('message')}")
                            return None
                    
                    elif response.status == 429:
                        logger.warning(f"HTTP 429 Rate limit hit for url: {url}. Retrying...")
                    elif response.status == 404:
                        return None
                    elif 500 <= response.status < 600:
                        logger.warning(f"Server error {response.status} for url: {url}. Retrying...")
                    else:
                        logger.error(f"HTTP error - url: {url}, status: {response.status}")
                        return None

                    delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e: # 네트워크 오류 재시도
                delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Network error for url {url}: {e}. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(delay)
            except Exception as e: # 기타 예외 로깅 후 종료
                logger.error(f"Unexpected error for url {url}: {e}", exc_info=True) 
                return None

        logger.error(f"Failed to fetch after {max_retries} attempts for url: {url}")
        return None

    async def get_character(self):
        """ 실험체 통계 데이터 가져오기 """
        character_url = f"{BASE_URL}{URLS['data']['character']}"
        character_levelup_url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"
        
        data_c = await self._fetch_json(character_url)
        data_cl = await self._fetch_json(character_levelup_url)
        
        if data_c and data_cl:
            return data_c, data_cl
        return None

    async def get_equipment(self):
        """ 장비 데이터 가져오기 """
        url_armor = f"{BASE_URL}{URLS['data']['item_armor']}"
        url_weapon = f"{BASE_URL}{URLS['data']['item_weapon']}"
        
        data_armor = await self._fetch_json(url_armor)
        data_weapon = await self._fetch_json(url_weapon)
        
        if data_armor and data_weapon:
            return data_armor, data_weapon
        return None
        
    async def get_trait(self) -> dict | None:
        """ 특성 데이터 가져오기 """
        url = f"{BASE_URL}{URLS['data']['trait']}"
        return await self._fetch_json(url)
        
    async def get_monster(self) -> dict | None:
        """ 야생동물 및 에픽 몬스터 데이터 가져오기 """
        url = f"{BASE_URL}{URLS['data']['monster']}"    
        return await self._fetch_json(url)
        
    async def get_area(self) -> dict | None:
        """ 지역 데이터 가져오기 """
        url = f"{BASE_URL}{URLS['data']['area']}"    
        return await self._fetch_json(url)
            
    async def get_char_lv(self) -> dict | None:
        """ 실험체 레벨업 능력치 데이터 가져오기 """
        url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"    
        return await self._fetch_json(url)

    async def get_l10n(self) -> List[str] | None:
        """ 텍스트 파일 가져오기(한국어) """
        url = f"{BASE_URL}{URLS['l10n']['korean']}"
        data = await self._fetch_json(url)
        if data and 'data' in data and 'l10Path' in data['data']: # l10Path가 있는 경우
            l10n_url = data['data']['l10Path']
            try:
                async with self.session.get(l10n_url) as response: # 텍스트 파일 직접 요청
                    if response.status == 200:
                        text_content = await response.text()
                        return text_content.splitlines()
            except Exception as e: 
                logger.error(f"get_l10n text file error: {e}")
        return None

    async def get_top_ranker(self, season_id: int, matching_mode: int, server_code: int) -> dict | None:
        """상위 랭커 목록(1,000명)을 조회합니다.

        Args:
            season_id: 시즌 ID (예: 35).
            matching_mode: 매칭 모드 (2=일반, 3=랭크, 6=코발트).
            server_code: 서버 코드 (10=asia, 20=na, 30=eu).

        Returns:
            랭커 정보가 담긴 딕셔너리. 실패 시 None.
        """
        url = f"{BASE_URL}{URLS['rank']['top'].format(season_id=season_id, matching_mode=matching_mode, server_code=server_code)}"
        data = await self._fetch_json(url, response_model=TopRankerResponse)
        return data.model_dump() if data else None

    async def fetch_user_by_nickname_async(self, nickname: str) -> Dict[str, Any] | None:
        """ 닉네임으로 사용자 정보 가져오기 """
        url = f"{BASE_URL}{URLS['user']['nickname']}"
        data = await self._fetch_json(url, params={'query': nickname})
        if data and "user" in data:
            user_obj = data["user"]
            try:
                UserBase.model_validate(user_obj)
                return user_obj
            except ValidationError as ve:
                logger.error(f"User validation error for {nickname}: {ve}")
        return None

    async def get_users_by_nickname_async(self, nicknames: List[str]) -> List[Dict[str, Any]]:
        """ 닉네임 목록으로 사용자 정보 조회 """
        tasks = [self.fetch_user_by_nickname_async(nickname) for nickname in nicknames]
        results = await asyncio.gather(*tasks)
        return [user for user in results if user]

    async def fetch_user_games(self, url: str) -> Tuple[int, dict]:
        """ 사용자 매치 기록 가져오기 """
        data = await self._fetch_json(url, response_model=MatchResponse)
        if data:
            return 200, data.model_dump()
        return 404, None 

    async def get_user_games_by_uid_async(self, users: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
        """여러 유저의 신규 매치 ID를 비동기로 수집합니다.

        각 유저의 last_match_id 이후의 랭크 매치만 수집하며,
        페이지네이션을 통해 모든 신규 매치를 조회합니다.

        Args:
            users: 유저 정보 리스트. 각 딕셔너리에 'uid', 'last_match_id' 포함.

        Yields:
            유저별 결과 딕셔너리:
                - {'uid': str, 'status': 'success', 'matches': List[int]}
                - {'uid': str, 'status': 'deactivated'} (탈퇴 유저, 닉네임 변경 등)
        """
        async def process_user(user) -> dict:
            """단일 사용자의 매치 기록을 처리합니다."""
            uid = user['uid']
            last_match_id = user['last_match_id']
            new_match_ids = []
            next_page = None
            
            while True:
                url = f"{BASE_URL}{URLS['user']['games'].format(uid=uid)}" # 사용자 매치 기록 URL
                if next_page: # 다음 페이지가 있는 경우 다음 페이지 조회
                    url += f"?next={next_page}"

                status, data = await self.fetch_user_games(url) # 매치 기록 호출

                if status == 404:
                    return {'uid': uid, 'status': 'deactivated'}
                
                if status != 200 or not data or "userGames" not in data:
                    break 

                stop_crawling = False
                for game in data["userGames"]: # 매치 id 수집
                    if game["gameId"] <= last_match_id:
                        stop_crawling = True
                        break
                    if game.get("matchingMode") == 3: # 매치 모드 필터링(Rank 게임만 가져옴)
                        new_match_ids.append(game["gameId"])
                
                if stop_crawling or not data.get('next'): # 다음 페이지가 없으면 종료
                    break
                
                next_page = data['next'] # 다음 페이지 업데이트
            
            return {'uid': uid, 'status': 'success', 'matches': new_match_ids}

        tasks = [process_user(user) for user in users]
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching user games"):
            user_result = await future
            yield user_result

    async def fetch_match_info(self, match_id: int):
        """ 단일 매치 정보 가져오기 """
        url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
        data = await self._fetch_json(url, response_model=MatchResponse)
        return match_id, data.model_dump() if data else None

    async def get_match_infos_async(self, match_ids: List[int], batch_size: int = 100) -> AsyncGenerator[Tuple[int, Any], None]:
        """매치 ID 목록에 대한 상세 정보를 배치 단위로 조회합니다.

        네트워크 부하를 분산하기 위해 batch_size 단위로 동시 요청하며,
        완료되는 순서대로 결과를 yield합니다.

        Args:
            match_ids: 조회할 매치 ID 리스트.
            batch_size: 동시 요청 수 (기본값: 100).

        Yields:
            (match_id, raw_data) 튜플. 실패한 매치는 yield되지 않음.
        """
        for i in range(0, len(match_ids), batch_size):
            batch = match_ids[i:i + batch_size]
            tasks = [self.fetch_match_info(match_id) for match_id in batch]
            for future in asyncio.as_completed(tasks):
                match_id, data = await future
                if data:
                    yield match_id, data
