from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import copy
import json
from collections import Counter
import pandas as pd
from scripts.config import CREDIT_ACQUISITIONS_PATH, CREDIT_EXPENDITURES_PATH, OBJECT_METRICS_PATH

def _load_json_mappings():
    try:
        with open(CREDIT_ACQUISITIONS_PATH, 'r', encoding='utf-8') as f:
            acq_data = json.load(f)
        with open(CREDIT_EXPENDITURES_PATH, 'r', encoding='utf-8') as f:
            exp_data = json.load(f)
        with open(OBJECT_METRICS_PATH, 'r', encoding='utf-8') as f:
            obj_data = json.load(f)
            
        return {
            "source_mapping": {k: tuple(v) for k, v in acq_data.get("source_mapping", {}).items()},
            "skip_cr_sources": set(acq_data.get("skip_cr_sources", [])),
            "console_item_mapping": {int(k): tuple(v) for k, v in exp_data.get("console_item_mapping", {}).items()},
            "credit_source_mapping": {k: tuple(v) for k, v in exp_data.get("credit_source_mapping", {}).items()},
            "special_material_keys": exp_data.get("special_material_keys", {}),
            "drone_season_9": {int(k): tuple(v) for k, v in exp_data.get("drone_item_mapping_season_9_plus", {}).items()},
            "drone_season_8": {int(k): tuple(v) for k, v in exp_data.get("drone_item_mapping_season_8", {}).items()},
            "robot_fixed_prices": {int(k): v for k, v in exp_data.get("robot_fixed_prices", {}).items()},
            "discount_info": {
                **exp_data.get("discount_info", {}),
                "target_items": set(exp_data.get("discount_info", {}).get("target_items", []))
            },
            "other_drone_item_cost": exp_data.get("other_drone_item_cost", {}),
            "object_metrics": {
                "direct_metrics": {k: tuple(v) for k, v in obj_data.get("direct_metrics", {}).items()},
                "kill_monster_metrics": obj_data.get("kill_monster_metrics", {}),
                "collect_log_metrics": obj_data.get("collect_log_metrics", {})
            }
        }
    except Exception as e:
        print(f"Failed to load mappings: {e}")
        return {}

MAPPINGS = _load_json_mappings()

def top_ranker_nicknames(data: dict) -> List[str]:
    """topRanks 데이터에서 상위 랭커의 nickname 리스트를 추출합니다.

    Args:
        data (dict): 'topRanks' 키를 포함한 랭킹 데이터 딕셔너리

    Returns:
        List[str]: 상위 유저들의 nickname 리스트
    """
    return [rank['nickname'] for rank in data.get('topRanks', [])]

def parse_match_info(data: dict) -> pd.DataFrame:
    """
    매치 기본 정보 파싱
    """
    if not data.get("userGames"):
        raise ValueError("No user games data found in the input")
    
    u = data["userGames"][0]
    start_dtm = datetime.strptime(u["startDtm"], "%Y-%m-%dT%H:%M:%S.%f%z")
    play_time = min(data["userGames"], key=lambda u: u["gameRank"])["totalTime"]
    match_expired_dtm = start_dtm + timedelta(seconds=play_time)
    
    match_info = {
        "match_id": u["gameId"],
        "season_id": u["seasonId"],
        "version_season": u.get("versionSeason", 0),
        "version_major": u["versionMajor"],
        "version_minor": u["versionMinor"],
        "matching_mode": u["matchingMode"],
        "matching_team_mode": u["matchingTeamMode"],
        "server_name": u["serverName"],
        "match_size": len(data["userGames"]),
        "start_dtm": start_dtm,
        "duration": play_time,
        "expired_tm": match_expired_dtm,
        "mmr_avg": u.get("mmrAvg", 0),
        "main_weather": u["mainWeather"],
        "sub_weather": u["subWeather"],
        "bot_added": u.get("botAdded", 0),
        "bot_remain": u.get("botRemain", 0),
        "safe_areas": u.get("safeAreas", 0),
        "restricted_area_accelerated": u.get("restrictedAreaAccelerated", 0),
    }
    
    return pd.DataFrame([match_info])

def parse_match_team_info(data: dict) -> pd.DataFrame:
    """
    팀 정보 파싱
    """
    team_info_list = []
    processed_team_ids = set()
    
    for u in data.get("userGames", []):
        team_id = u["teamNumber"]
        if team_id in processed_team_ids:
            continue
            
        is_older_version = u["versionMajor"] < 44
        
        team_info = {
            "match_id": u["gameId"],
            "team_number": team_id,
            "game_rank": u["gameRank"],
            "team_kill": u.get("teamKill", 0),
            "total_field_kill": u.get("totalFieldKill", 0),
            "team_elimination": u["teamElimination"],
            "team_down": u["teamDown"],
            "team_repeat_down": u.get("teamRepeatDown", 0),
            "team_battle_zone_down": u.get("teamBattleZoneDown", 0),
            "escape_state": u["escapeState"],
        }
        
        if is_older_version:
            team_info.update({
                "team_down_cannot_eliminate": u.get("teamDownInAutoResurrection", 0),
                "team_down_can_eliminate": u.get("teamDownDeactiveAutoResurrection", 0),
                "team_repeat_down_cannot_eliminate": u.get("teamRepeatDownInAutoResurrection", 0),
                "team_repeat_down_can_eliminate": u.get("teamRepeatDownDeactiveAutoResurrection", 0)
            })
        else:
            team_info.update({
                "team_down_cannot_eliminate": u.get("teamDownCanNotEliminate", 0),
                "team_down_can_eliminate": u.get("teamDownCanEliminate", 0),
                "team_repeat_down_cannot_eliminate": u.get("teamRepeatDownCanNotEliminate", 0),
                "team_repeat_down_can_eliminate": u.get("teamRepeatDownCanEliminate", 0)
            })
        
        team_info_list.append(team_info)
        processed_team_ids.add(team_id)
    
    return pd.DataFrame(team_info_list)

def parse_match_user_start(data: dict) -> pd.DataFrame:
    """
    게임 시작 전 유저 정보와 게임 정보를 파싱
    """
    user_basic_list = [
        {
            "match_id": u["gameId"],
            "uid": u["uid"],
            "nickname": u["nickname"],
            "character_num": u["characterNum"],
            "language": u.get("language", "None"),
            "team_number": u["teamNumber"],
            "skin_code": u["skinCode"],
            "premade": u.get("preMade", 0),
            "except_premade_team": u["exceptPreMadeTeam"],
            "route_id_of_start": u.get("routeIdOfStart", 0),
            "place_of_start": int(u["placeOfStart"]),
            "using_default_game_option": u.get("usingDefaultGameOption", True),
            "premade_matching_type": u.get("premadeMatchingType", 0),
            "tactical_skill_id": u.get("tacticalSkillGroup",0), 
            "ml_bot": u.get("mlbot", False)
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_basic_list)

def parse_match_user_end(data: dict) -> pd.DataFrame:
    """
    게임 종료 후 유저 기본 정보 파싱
    """
    user_basic_list = [
        {
            "match_id": u["gameId"],
            "uid": u["uid"],
            "victory": 1 if u.get("victory", False) else 0,
            "play_time": u["playTime"],
            "watch_time": u.get("watchTime", 0),
            "total_time": u.get("totalTime"),
            "time_spent_in_briefing_room": u.get("timeSpentInBriefingRoom", 0),
            "craft_uncommon": u.get("craftUncommon", 0),
            "craft_rare": u.get("craftRare", 0),
            "craft_epic": u.get("craftEpic", 0),
            "craft_legend": u.get("craftLegend", 0),
            "craft_mythic": u.get("craftMythic", 0),
            "use_hyperloop": u.get("useHyperLoop", 0),
            "use_security_console": u.get("useSecurityConsole", 0),
            "break_count": u.get("breakCount", 0),
            "enter_dimension_rift": u.get("enterDimensionRift",0),
            "enter_dimension_empowered_rift": u.get("enterDimensionEmpoweredRift",0),
            "win_dimension_rift": u.get("winFromDimensionRift",0),
            "win_dimension_empowered_rift": u.get("winFromDimensionEmpoweredRift",0),
            "resurrectionkit_count": u.get("resurrectionKitUsageCount",0),
            "resurrectionkit_credit_count": u.get("resurrectionKitCreditUsageCount",0),
            "fishing_count": u.get("fishingCount", 0),
            "emoticon_count": u.get("useEmoticonCount", 0),
            "used_pairloop": u.get("usedPairLoop", 0),
            "give_up": u.get("giveUp", 0),
            "team_spectator": u.get("teamSpectator", 0),
            "is_leaving_before_credit_revival_terminate": u.get("isLeavingBeforeCreditRevivalTerminate", False),
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_basic_list)

def parse_match_user_combat(data: dict) -> pd.DataFrame:
    """
    유저 전투 정보 파싱
    """
    user_combat_list = [
        {
            "match_id": u["gameId"],
            "uid": u["uid"],
            "character_level": u["characterLevel"],
            "tactical_skill_level": u.get("tacticalSkillLevel",0),
            "player_kill": u.get("playerKill", 0),
            "player_assistant": u.get("playerAssistant", 0),
            "player_deaths": u.get("playerDeaths", 0),
            "monster_kill": u.get("monsterKill", 0),
            "kills_phase_one": u.get("killsPhaseOne", 0),
            "kills_phase_two": u.get("killsPhaseTwo", 0),
            "kills_phase_three": u.get("killsPhaseThree", 0),
            "deaths_phase_one": u.get("deathsPhaseOne", 0),
            "deaths_phase_two": u.get("deathsPhaseTwo", 0),
            "deaths_phase_three": u.get("deathsPhaseThree", 0),
            "terminate_count": u.get("terminateCount", 0),
            "terminate_count_cannot_eliminate": u.get("terminateCountCanNotEliminate", 0),
            "clutch_count": u.get("clutchCount", 0),
            "unknown_kill": u.get("unknownKill", 0),
            "cc_time_to_player": u.get("ccTimeToPlayer", 0.0),
            "credit_revival_count": u.get("creditRevivalCount", 0),
            "credit_revived_others_count": u.get("creditRevivedOthersCount", 0),
            "reunited_count": u.get("reunitedCount", 0),
            "tactical_skill_count": u.get("tacticalSkillUseCount", 0),
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_combat_list)

def parse_match_user_trait(data: dict) -> pd.DataFrame:
    """
    유저 특성 정보 파싱
    """
    user_traits_list = []
    for u in data.get("userGames", []):
        match_id = u["gameId"]
        uid = u["uid"]
        for trait_id in u.get("traitFirstSub", []):
            user_traits_list.append({"match_id": match_id, "uid": uid, "trait_id": int(trait_id), "trait_type": "first_sub"})
        for trait_id in u.get("traitSecondSub", []):
            user_traits_list.append({"match_id": match_id, "uid": uid, "trait_id": int(trait_id), "trait_type": "second_sub"})
    return pd.DataFrame(user_traits_list)

def parse_match_user_damage(data: dict) -> pd.DataFrame:
    """
    유저 데미지 정보 파싱
    """
    user_damage_list = [
        {
            "match_id": u["gameId"],
            "uid": u["uid"],
            "damage_to_player_total": u.get("damageToPlayer", 0),
            "damage_to_player_basic": u.get("damageToPlayer_basic", 0),
            "damage_to_player_skill": u.get("damageToPlayer_skill", 0),
            "damage_to_player_item_skill": u.get("damageToPlayer_itemSkill", 0),
            "damage_to_player_direct": u.get("damageToPlayer_direct", 0),
            "damage_to_player_trap": u.get("damageToPlayer_trap", 0),
            "damage_to_player_unique_skill": u.get("damageToPlayer_uniqueSkill", 0),
            "damage_to_player_shield": u.get("damageToPlayer_Shield", 0),
            "damage_from_player_total": u.get("damageFromPlayer", 0),
            "damage_from_player_basic": u.get("damageFromPlayer_basic", 0),
            "damage_from_player_skill": u.get("damageFromPlayer_skill", 0),
            "damage_from_player_item_skill": u.get("damageFromPlayer_itemSkill", 0),
            "damage_from_player_direct": u.get("damageFromPlayer_direct", 0),
            "damage_from_player_trap": u.get("damageFromPlayer_trap", 0),
            "damage_from_player_unique_skill": u.get("damageFromPlayer_uniqueSkill", 0),
            "damage_to_monster_total": u.get("damageToMonster", 0),
            "damage_to_monster_basic": u.get("damageToMonster_basic", 0),
            "damage_to_monster_skill": u.get("damageToMonster_skill", 0),
            "damage_to_monster_item_skill": u.get("damageToMonster_itemSkill", 0),
            "damage_to_monster_direct": u.get("damageToMonster_direct", 0),
            "damage_to_monster_trap": u.get("damageToMonster_trap", 0),
            "damage_to_monster_unique_skill": u.get("damageToMonster_uniqueSkill", 0),
            "damage_from_monster_total": u.get("damageFromMonster", 0),
            "damage_offseted_by_shield_player": u.get("damageOffsetedByShield_Player", 0),
            "damage_offseted_by_shield_monster": u.get("damageOffsetedByShield_Monster", 0),
            "damage_to_guide_robot": u.get("damageToGuideRobot", 0),
            "heal_amount": u.get("healAmount", 0),
            "team_recover": u.get("teamRecover", 0),
            "protect_absorb": u.get("protectAbsorb", 0)
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_damage_list)

def parse_match_user_credit_acquisitions(data: dict) -> pd.DataFrame:
    """
    크레딧 획득 정보 파싱
    """
    acquisition_list = []
    source_mapping = MAPPINGS.get("source_mapping", {})
    skip_cr_sources = MAPPINGS.get("skip_cr_sources", set())
    
    for u in data.get("userGames", []):
        for source, amount in u.get("creditSource", {}).items():
            if source in skip_cr_sources or amount <= 0:
                continue
            acq_type, src_cat = source_mapping.get(source, ("special", "unknown"))
            acquisition_list.append({
                "match_id": u["gameId"], "uid": u["uid"], "acquisition_source": source,
                "acquisition_type": acq_type, "credit_amount": float(amount), "source_category": src_cat
            })
    return pd.DataFrame(acquisition_list)

def parse_match_user_credit_expenditures(data: dict) -> pd.DataFrame:
    """
    크레딧 소모 정보 파싱 (시간 복잡도 개선)
    """
    expenditure_list = []

    # MAPPINGS에서 데이터 로드
    credit_source_mapping = MAPPINGS.get("credit_source_mapping", {})
    console_item_mapping = MAPPINGS.get("console_item_mapping", {})
    special_material_keys = MAPPINGS.get("special_material_keys", {})
    robot_fixed_prices = MAPPINGS.get("robot_fixed_prices", {})
    discount_info = MAPPINGS.get("discount_info", {})
    
    discount_trait_code = discount_info.get("trait_code")
    discount_amount = discount_info.get("amount", 0)
    discount_target_items = discount_info.get("target_items", set())

    # 드론 아이템 코드 대상 매핑
    is_season_9_plus = data['userGames'][0]['versionSeason'] > 8
    drone_item_mapping = MAPPINGS.get("drone_season_9", {}) if is_season_9_plus else MAPPINGS.get("drone_season_8", {})
    other_item_cr = MAPPINGS.get("other_drone_item_cost", {}).get("season_9_plus" if is_season_9_plus else "season_8", 10)

    for u in data.get("userGames", []):
        match_id = u["gameId"]
        uid = u["uid"]
        
        # 유저별 소모 아이템 순번 추적용
        item_counter = Counter()

        # 할인 로직 적용
        kiosk_prices = copy.deepcopy(console_item_mapping)
        user_traits = u.get("traitFirstSub", []) + u.get("traitSecondSub", [])
        if discount_trait_code in user_traits:
            for item_code in discount_target_items:
                if item_code in kiosk_prices:
                    name, type, cost = kiosk_prices[item_code]
                    kiosk_prices[item_code] = (name, type, cost - discount_amount)
        
        console_items_log = u.get("itemTransferredConsole", []).copy()
        special_material_spent = {key: u.get(key, 0) for key in special_material_keys}
        item_code_to_cr_key = {v: k for k, v in special_material_keys.items()}
        robot_purchase_log = []

        for item_code in console_items_log:
            if item_code in item_code_to_cr_key:
                cr_key = item_code_to_cr_key[item_code]
                name, exp_type, price = kiosk_prices[item_code]
                
                if special_material_spent[cr_key] >= price > 0:
                    special_material_spent[cr_key] -= price
                    item_counter[name] += 1
                    expenditure_list.append({
                        "match_id": match_id, "uid": uid,
                        "expenditure_item": name, "expenditure_type": exp_type,
                        "credit_amount": int(price), "usage_count": 1,
                        "order_seq": item_counter[name]
                    })
                else:
                    robot_purchase_log.append(item_code)
            else:
                robot_purchase_log.append(item_code)

        # --- 로봇 구매 처리 로직 ---
        remaining_items = [item for item in robot_purchase_log if item != 999999]
        remaining_item_counts = Counter(remaining_items)
        
        for item_code, count in remaining_item_counts.items():
            if item_code in console_item_mapping:
                name, _, original_price = console_item_mapping[item_code]
                price = robot_fixed_prices.get(item_code, original_price)

                item_counter[name] += 1
                expenditure_list.append({
                    "match_id": match_id, "uid": uid,
                    "expenditure_item": name, "expenditure_type": "robot_item",
                    "credit_amount": int(count * price), "usage_count": count,
                    "order_seq": item_counter[name]
                })

        # --- 기타 소모 항목 처리 ---
        credit_source = u.get("creditSource", {})
        for source_key, (exp_type, default_count) in credit_source_mapping.items():
            amount = credit_source.get(source_key, 0)
            if amount > 0:
                 item_counter[source_key] += 1
                 expenditure_list.append({
                    "match_id": match_id, "uid": uid,
                    "expenditure_item": source_key, "expenditure_type": exp_type,
                    "credit_amount": int(amount), "usage_count": u.get("creditRevivalCount", 1) if source_key == "KioskResurrection" else default_count,
                    "order_seq": item_counter[source_key]
                })

        # --- 드론 아이템 처리 로직 ---
        item_transferred_drone = u.get("itemTransferredDrone", [])
        if item_transferred_drone:
            drone_item_counts = Counter(item_transferred_drone)
            for item_code, (name, exp_type, cost) in drone_item_mapping.items():
                count = drone_item_counts.pop(item_code, 0)
                if count > 0:
                    item_counter[name] += 1
                    expenditure_list.append({
                        "match_id": match_id, "uid": uid,
                        "expenditure_item": name, "expenditure_type": exp_type,
                        "credit_amount": int(count * cost), "usage_count": count,
                        "order_seq": item_counter[name]
                    })
            
            other_items_count = sum(drone_item_counts.values())
            if other_items_count > 0:
                item_counter["etc"] += 1
                expenditure_list.append({
                    "match_id": match_id, "uid": uid,
                    "expenditure_item": "etc", "expenditure_type": "remotedrone_item",
                    "credit_amount": int(other_items_count * other_item_cr), "usage_count": other_items_count,
                    "order_seq": item_counter["etc"]
                })
    return pd.DataFrame(expenditure_list)

def parse_match_user_stats(data: dict) -> pd.DataFrame:
    """
    유저 스탯 정보 파싱
    """
    user_stats_list = [
        {
            "match_id": u["gameId"], "uid": u["uid"],
            "max_hp": u.get("maxHp", 0), "hp_regen": u.get("hpRegen", 0.0),
            "attack_power": u.get("attackPower", 0), "attack_speed": u.get("attackSpeed", 0.0),
            "defense": u.get("defense", 0), "skill_amp": u.get("skillAmp", 0),
            "move_speed": u.get("moveSpeed", 0.0), "ooc_move_speed": float(u.get("outOfCombatMoveSpeed", 0.0)),
            "sight_range": u.get("sightRange", 0), "attack_range": u.get("attackRange",0.0),
            "adaptive_force": u.get("adaptiveForce", 0.0), "adaptive_force_attack": u.get("adaptiveForceAttack", 0.0),
            "adaptive_force_amp": u.get("adaptiveForceAmplify", 0.0), "critical_strike_chance": u.get("criticalStrikeChance", 0.0),
            "critical_damage": int(u.get("criticalStrikeDamage", 0)), "cooldown_reduction": int(u.get("coolDownReduction", 0)/100),
            "life_steal": int(100*u.get("lifesteal", 0)), "normal_life_steal": int(100*u.get("normalLifesteal",0)),
            "skill_life_steal": int(100*u.get("skillLifesteal",0))
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_stats_list)

def parse_match_user_equipment(data: dict) -> pd.DataFrame:
    """
    유저 장비 정보 파싱
    """
    def none_if_zero(val):
        if val is None or val == 0 or val == -1: return None
        if isinstance(val, list): return val[0] if val else None
        return val

    user_equipment_list = [
        {
            "match_id": u["gameId"], "uid": u["uid"],
            "first_weapon": none_if_zero(u.get("equipFirstItemForLog", {}).get("0")),
            "first_chest": none_if_zero(u.get("equipFirstItemForLog", {}).get("1")),
            "first_head": none_if_zero(u.get("equipFirstItemForLog", {}).get("2")),
            "first_arm": none_if_zero(u.get("equipFirstItemForLog", {}).get("3")),
            "first_leg": none_if_zero(u.get("equipFirstItemForLog", {}).get("4")),
            "last_weapon": none_if_zero(u.get("equipment", {}).get("0")),
            "last_chest": none_if_zero(u.get("equipment", {}).get("1")),
            "last_head": none_if_zero(u.get("equipment", {}).get("2")),
            "last_arm": none_if_zero(u.get("equipment", {}).get("3")),
            "last_leg": none_if_zero(u.get("equipment", {}).get("4")),
            "best_weapon": u.get("bestWeapon", 0),
            "best_weapon_level": u.get("bestWeaponLevel", 0)
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_equipment_list)

def parse_match_user_mmr(data: dict) -> pd.DataFrame:
    """
    MMR 정보 파싱
    """
    user_mmr_list = [
        {
            "match_id": u["gameId"], "uid": u["uid"],
            "mmr_before": u.get("mmrBefore", 0), "mmr_after": u.get("mmrAfter", 0),
            "mmr_gain": u.get("mmrGain", 0), "mmr_gain_in_game": u.get("mmrGainInGame", 0),
            "mmr_loss_entry_cost": u.get("mmrLossEntryCost", 0), "rank_point": u.get("rankPoint", 0)
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_mmr_list)

def parse_object(data: dict) -> pd.DataFrame:
    """Long Format으로 오브젝트 정보 파싱"""
    object_list = []
    
    obj_mappings = MAPPINGS.get("object_metrics", {})
    direct_metrics = obj_mappings.get("direct_metrics", {})
    kill_monster_metrics = obj_mappings.get("kill_monster_metrics", {})
    collect_log_metrics = obj_mappings.get("collect_log_metrics", {})

    for u in data.get("userGames", []):
        match_id, uid = u["gameId"], u["uid"]
        for name, (key, mtype) in direct_metrics.items():
            if (value := u.get(key, 0)) > 0:
                object_list.append({"match_id": match_id, "uid": uid, "metric_type": mtype, "metric_name": name, "value": value})
        for key, name in kill_monster_metrics.items():
            value = u.get("killMonsters", {}).get(key, 0)
            if name == "kill_wickline": value = 1 if value > 0 else 0
            if value > 0:
                object_list.append({"match_id": match_id, "uid": uid, "metric_type": "kill_boss", "metric_name": name, "value": value})
        collect_log = u.get("collectItemForLog", [])
        for idx_str, name in collect_log_metrics.items():
            idx = int(idx_str)
            if len(collect_log) > idx and (value := collect_log[idx]) > 0:
                object_list.append({"match_id": match_id, "uid": uid, "metric_type": "collect_special", "metric_name": name, "value": value})
        for key, value in u.get("activeInstallation", {}).items():
            if value > 0:
                object_list.append({"match_id": match_id, "uid": uid, "metric_type": "installation", "metric_name": int(key), "value": value})
    return pd.DataFrame(object_list)

def parse_match_user_credit_time(data: dict) -> pd.DataFrame:
    """분당 크레딧 정보 파싱"""
    user_credit_time_list = []
    for u in data.get("userGames", []):
        for minute in range(20):
            used = u["usedVFCredits"][minute]
            gain = u["totalVFCredits"][minute]
            if used != 0 or gain != 0:
                user_credit_time_list.append({"match_id": u["gameId"], "uid": u["uid"], "minute": minute, "used_credit": used, "gain_credit": gain})
    return pd.DataFrame(user_credit_time_list)

def parse_match_user_sight(data: dict) -> pd.DataFrame:
    """시야 정보 파싱"""
    user_sight_list = [
        {
            "match_id": u["gameId"], "uid": u["uid"],
            "sight_score": u["viewContribution"], "camera_setup": u["addTelephotoCamera"],
            "camera_remove": u["removeTelephotoCamera"], "emp_drone_setup": u["useEmpDrone"],
            "basic_drone_setup": u["useReconDrone"]
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_sight_list)

def parse_match_data(data: dict) -> Dict[str, pd.DataFrame]:
    """
    전체 매치 데이터 파싱
    """
    try:
        # match_user_start를 먼저 파싱하여 스노우볼링을 위한 uid/nickname mapping을 생성
        df_user_start = parse_match_user_start(data)
        parsed_dfs = {
            "match_info": parse_match_info(data),
            "match_team_info": parse_match_team_info(data),
            "match_user_start": df_user_start,
            "match_user_end": parse_match_user_end(data),
            "match_user_trait": parse_match_user_trait(data),
            "match_user_combat": parse_match_user_combat(data),
            "match_user_damage": parse_match_user_damage(data),
            "match_user_credit_acquisitions": parse_match_user_credit_acquisitions(data),
            "match_user_credit_expenditures": parse_match_user_credit_expenditures(data),
            "match_user_object": parse_object(data),
            "match_user_credit_time": parse_match_user_credit_time(data),
            "match_user_stats": parse_match_user_stats(data),
            "match_user_sight": parse_match_user_sight(data),
            "match_user_equipment": parse_match_user_equipment(data),
            "match_user_mmr": parse_match_user_mmr(data)
        }
        return parsed_dfs
    except Exception as e:
        print(f"Error parsing match data: {e}")
        raise