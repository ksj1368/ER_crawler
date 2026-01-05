"""
Meta Information Parsing Module for Eternal Return Analytics

이터널 리턴의 메타 정보 JSON 파일들(캐릭터, 아이템, 몬스터 등)을 파싱하여 
MySQL 스키마에 맞는 형태로 변환하는 모듈

지원하는 JSON 파일:
- Character.json: 캐릭터 기본 정보
- CharacterLevelUpStat.json: 캐릭터 레벨업 스탯 정보
- ItemWeapon.json: 무기 아이템 정보
- ItemArmor.json: 방어구 아이템 정보  
- Monster.json: 몬스터 정보

"""
from typing import Dict, List, Any
import json
from scripts.crawler import ERAPIClient
from scripts.config import GAME_METADATA_PATH

def _load_game_metadata():
    try:
        with open(GAME_METADATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load game metadata: {e}")
        return {}

GAME_METADATA = _load_game_metadata()

def weapon_type() -> Dict[str, Any]:
    return {int(k): v for k, v in GAME_METADATA.get("weapon_types", {}).items()}

def tactical_type() -> Dict[str, Any]:
    return {int(k): v for k, v in GAME_METADATA.get("tactical_skills", {}).items()}

def parse_area_info(data: Dict[str, Any], season: int = 8, major_version: int = 1, minor_version: int = 50) -> List[Dict[str, Any]]:
    area_list =[]
    for area in data.get('data', []):
        area_info = {
            'season': season,
            'major_version': major_version,
            'minor_version': minor_version,
            'area_id': area['code'],
            'area_name': area['name']
        }
        area_list.append(area_info)
    
    return area_list
    
def parse_from_l10n(data: list, parse_key: str, season: int = 8, major_version: int = 1, minor_version: int = 50) -> List[Dict[str, Any]]:
    """특정 구분자(┃)로 구분된 텍스트에서 특성 관련 정보를 trait_id-trait_name 형식의 딕셔너리로 변환

    Args:
        data (list): 특성 정보가 담긴 데이터
        txt_mapping (Dict[str, str]): 특성 코드에 대응하는 이름 매핑 딕셔너리

    Returns:
        List[Dict]: 각 특성의 ID와 이름을 담은 딕셔너리 리스트
    """    
    data_list = []    
    txt_key = f"{parse_key.capitalize()}/Name/"
    for d in data:
        if txt_key in d:
            parts = d.replace(f"{parse_key.capitalize()}/Name/", "").split("┃")
            if len(parts) >= 2:
                data_id, data_name = parts[0], parts[1]
                parsing_dict = {
                    'season': season,
                    'major_version': major_version,
                    'minor_version': minor_version,
                    f'{parse_key}_id': int(data_id),
                    f"{parse_key}_name": data_name,
                }      
                data_list.append(parsing_dict)

    return data_list

def parse_character_info(data: Dict[str, Any], season: int = 8, major_version: int = 1, minor_version: int = 50) -> List[Dict[str, Any]]:
    """
    Character.json을 파싱하여 characterinfo 테이블 형태로 변환
    
    Args:
        data (Dict): Character.json 로드 결과
        major_version (int): 메이저 버전 (기본값: 1)
        minor_version (int): 마이너 버전 (기본값: 50)
        
    Returns:
        List[Dict]: characterinfo 테이블용 레코드 리스트
    """
    character_list = []
    
    for char in data.get('data', []):
        character_info = {
            'character_id': char['code'],
            'character_name': char['name'],
            'season': season,
            'major_version': major_version,
            'minor_version': minor_version,
            'archetype_primary': char.get('charArcheType1', 'Unknown'),
            'archetype_secondary': char.get('charArcheType2') or None,  # None이면 NULL로 저장
            'weapon_range_type': char.get('weaponRangeType', 'Unknown'),
            'base_max_hp': int(char.get('maxHp', 0)),
            'base_attack_power': int(char.get('attackPower', 0)),
            'base_defense': int(char.get('defense', 0)),
            'base_skill_amp': int(char.get('skillAmp', 0)),
            'base_hp_regen': float(char.get('hpRegen', 0.0)),
            'base_attack_speed': float(char.get('attackSpeed', 0.0)),
            'base_move_speed': float(char.get('moveSpeed', 0.0)),
            'base_sight_range': float(char.get('sightRange', 0.0))
        }
        character_list.append(character_info)
    
    return character_list


def parse_character_levelup_stats(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    CharacterLevelUpStat.json을 파싱하여 characterlevelupstats 테이블 형태로 변환
    
    Args:
        data (Dict): CharacterLevelUpStat.json 로드 결과
        
    Returns:
        List[Dict]: characterlevelupstats 테이블용 레코드 리스트
    """
    levelup_list = []
    
    for char in data.get('data', []):
        levelup_info = {
            'character_id': char['code'],
            'levelup_max_hp': float(char.get('maxHp', 0.0)),
            'levelup_attack_power': float(char.get('attackPower', 0.0)),
            'levelup_defense': float(char.get('defense', 0.0)),
            'levelup_hp_regen': float(char.get('hpRegen', 0.0)),
        }
        levelup_list.append(levelup_info)
    
    return levelup_list


def parse_item_weapon(data: Dict[str, Any], season: int = 8, major_version: int = 1, minor_version: int = 50) -> List[Dict[str, Any]]:
    """
    ItemWeapon.json을 파싱하여 itemweapon 테이블 형태로 변환
    
    Args:
        data (Dict): ItemWeapon.json 로드 결과
        major_version (int): 메이저 버전 (기본값: 1)
        minor_version (int): 마이너 버전 (기본값: 50)
        
    Returns:
        List[Dict]: itemweapon 테이블용 레코드 리스트
    """
    weapon_list = []
    
    for weapon in data.get('data', []):
        weapon_info = {
            'item_id': weapon['code'],
            'item_name': weapon['name'],
            'season': season,
            'major_version': major_version,
            'minor_version': minor_version,
            'weapon_type': weapon.get('weaponType', 'Unknown'),
            'item_grade': weapon.get('itemGrade', 'Unknown'),
            'manufacturable_type': int(weapon.get('manufacturableType', 0)),
            'attack_power': int(weapon.get('attackPower', 0)),
            'defense': int(weapon.get('defense', 0)),
            'skill_amp': int(weapon.get('skillAmp', 0)),
            'max_hp': int(weapon.get('maxHp', 0)),
            'attack_speed_ratio': int(weapon.get('attackSpeedRatio', 0)),
            'critical_strike_chance': int(weapon.get('criticalStrikeChance', 0)),
            'critical_strike_damage': int(weapon.get('criticalStrikeDamage', 0)),
            'cooldown_reduction': int(weapon.get('cooldownReduction', 0)),
            'life_steal': int(weapon.get('lifeSteal', 0)),
            'attack_range': float(weapon.get('attackRange', 0.0))
        }
        weapon_list.append(weapon_info)
    
    return weapon_list


def parse_item_armor(data: Dict[str, Any], season: int = 8,major_version: int = 1, minor_version: int = 50) -> List[Dict[str, Any]]:
    """
    ItemArmor.json을 파싱하여 itemarmor 테이블 형태로 변환
    
    Args:
        data (Dict): ItemArmor.json 로드 결과
        major_version (int): 메이저 버전 (기본값: 1)
        minor_version (int): 마이너 버전 (기본값: 50)
        
    Returns:
        List[Dict]: itemarmor 테이블용 레코드 리스트
    """
    armor_list = []
    
    for armor in data.get('data', []):
        armor_info = {
            'item_id': armor['code'],
            'item_name': armor['name'],
            'season': season,
            'major_version': major_version,
            'minor_version': minor_version,
            'item_type': armor.get('itemType', 'Unknown'),
            'armor_type': armor.get('armorType', 'Unknown'),
            'item_grade': armor.get('itemGrade', 'Unknown'),
            'manufacturable_type': int(armor.get('manufacturableType', 0)),
            'attack_power': int(armor.get('attackPower', 0)),
            'defense': int(armor.get('defense', 0)),
            'skill_amp': int(armor.get('skillAmp', 0)),
            'max_hp': int(armor.get('maxHp', 0)),
            #'max_sp': int(armor.get('maxSp', 0)),
            'hp_regen': int(armor.get('hpRegen', 0)),
            #'sp_regen': int(armor.get('spRegen', 0)),
            'attack_speed_ratio': int(armor.get('attackSpeedRatio', 0)),
            'critical_strike_chance': int(armor.get('criticalStrikeChance', 0)),
            'critical_strike_damage': int(armor.get('criticalStrikeDamage', 0)),
            'cooldown_reduction': int(armor.get('cooldownReduction', 0)),
            'life_steal': int(armor.get('lifeSteal', 0)),
            'move_speed': float(armor.get('moveSpeed', 0.0)),
            'move_speed_ratio': float(armor.get('moveSpeedRatio', 0.0))
        }
        armor_list.append(armor_info)
    
    return armor_list


def parse_monster_info(data: Dict[str, Any], season: int = 8, major_version: int = 1, minor_version: int = 50) -> List[Dict[str, Any]]:
    """
    Monster.json을 파싱하여 monsterinfo 테이블 형태로 변환하고 중복을 제거합니다.
    
    Args:
        data (Dict): Monster.json 로드 결과
        
    Returns:
        List[Dict]: monsterinfo 테이블용 레코드 리스트 (중복 제거됨)
    """
    monster_map = {} # monster_id를 키로 사용하여 중복 제거
    
    for monster in data.get('data', []):
        code = monster['code']
        if code not in monster_map:
            monster_info = {
                'season': season,
                'major_version': major_version,
                'minor_version': minor_version,
                'monster_id': code,
                'monster_name': monster['monster'],
                'monster_grade': monster.get('grade', 'Unknown'),
                'is_mutant': bool(monster.get('isMutant', False)),
                'max_hp': int(monster.get('maxHp', 0)),
                'attack_power': int(monster.get('attackPower', 0)),
                'defense': int(monster.get('defense', 0)),
                'attack_speed': float(monster.get('attackSpeed', 0.0)),
                'move_speed': float(monster.get('moveSpeed', 0.0)),
                'attack_range': float(monster.get('attackRange', 0.0)),
                'sight_range': int(monster.get('sightRange', 0)),
                'gain_exp': int(monster.get('gainExp', 0))
            }
            monster_map[code] = monster_info
    
    return list(monster_map.values())


async def parse_all_meta_files(
    client: ERAPIClient,
    l10n_data: List[str],  # l10n 데이터를 인자로 추가
    season: int = 8, 
    major_version: int = 1, 
    minor_version: int = 50
) -> Dict[str, List[Dict[str, Any]]]:
    """
    모든 메타 정보 JSON 파일을 파싱하여 테이블별 레코드를 반환
    """
    results = {}
    a, w = await client.get_equipment()
    char_data = await client.get_character()
    results['character_info'] = parse_character_info(char_data[0], season, major_version, minor_version)
    results['character_levelup_stats'] = parse_character_levelup_stats(await client.get_char_lv())  
    results['item_weapon'] = parse_item_weapon(w, season, major_version, minor_version)  
    results['item_armor'] = parse_item_armor(a, season, major_version, minor_version)  
    results['monster_info'] = parse_monster_info(await client.get_monster(), season, major_version, minor_version)  
    results['area_info'] = parse_area_info(await client.get_area(), season, major_version, minor_version)
    results['weather_info'] = parse_from_l10n(l10n_data, 'weather', season, major_version, minor_version)
    results['installation_info'] = parse_from_l10n(l10n_data, 'installation', season, major_version, minor_version)
    results['trait_info'] = parse_from_l10n(l10n_data, 'trait', season, major_version, minor_version)
    
    return results