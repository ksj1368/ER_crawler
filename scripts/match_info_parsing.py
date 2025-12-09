from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import copy
from collections import Counter
import pandas as pd

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
    게임 시작 전 유저 기본 정보 파싱
    """
    user_basic_list = [
        {
            "match_id": u["gameId"],
            "user_id": u["userNum"],
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
            "mlbot": u.get("mlbot", False)
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
            "user_id": u["userNum"],
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
            "user_id": u["userNum"],
            #"character_num": u["characterNum"],
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
        user_id = u["userNum"]
        for trait_id in u.get("traitFirstSub", []):
            user_traits_list.append({"match_id": match_id, "user_id": user_id, "trait_id": int(trait_id), "trait_type": "first_sub"})
        for trait_id in u.get("traitSecondSub", []):
            user_traits_list.append({"match_id": match_id, "user_id": user_id, "trait_id": int(trait_id), "trait_type": "second_sub"})
    return pd.DataFrame(user_traits_list)

def parse_match_user_damage(data: dict) -> pd.DataFrame:
    """
    유저 데미지 정보 파싱
    """
    user_damage_list = [
        {
            "match_id": u["gameId"],
            "user_id": u["userNum"],
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
    source_mapping = {
        "KillChicken": ("monster", "Monster"), "KillBat": ("monster", "Monster"),
        "KillWolf": ("monster", "Monster"), "KillBoar": ("monster", "Monster"),
        "KillWildDog": ("monster", "Monster"), "KillBear": ("monster", "Monster"),
        "KillRaven": ("monster", "Monster"), "KillAttackDrone": ("monster", "Monster"),
        "KillMutantChicken": ("monster", "Monster"), "KillMutantBat": ("monster", "Monster"),
        "KillMutantWolf": ("monster", "Monster"), "KillMutantBoar": ("monster", "Monster"),
        "KillMutantWildDog": ("monster", "Monster"), "KillMutantBear": ("monster", "Monster"),
        "KillMutantRaven": ("monster", "Monster"), "KillAlpha": ("monster", "Epic"),
        "KillOmega": ("monster", "Epic"), "KillGamma": ("monster", "Epic"),
        "KillWickline": ("monster", "Boss"), "KillPlayerMerge": ("player", "player"),
        "KillAssistDivideContribute": ("player", "player"), "GoldSecurityConsoleAccess": ("env", "env"),
        "DoorConsoleAccess": ("env", "env"), "KillOrb": ("env", "orb"),
        "AcquireLumiCredit": ("env", "lumi"), "PreliminaryPhase": ("timebased", "game"),
        "TimeElapsedCompensationByMiliSecond": ("timebased", "game"),
        "TimeElapsedCreditBonusByMiliSecond": ("timebased", "game"),
        "ItemBounty": ("bounty", "special"), "ItemBountyByItemCode": ("bounty", "special"),
        "GetBySkill": ("special", "skill"), "TraitSkillCoinToss": ("special", "trait"),
        "crGetCreditBonus": ("special", "skill"),
        "AcquireBoriCredit": ("env", "bori"),
    }
    skip_cr_sources = {"KioskSpecialMaterial", "guideRobotFlagShip", "guideRobotSignature", "guideRobotRadial", "KioskRemoteDroneMySelf", "KioskResurrection", "KioskRemoteDroneAlly", "TacticalSkillUpgrade"}
    
    for u in data.get("userGames", []):
        for source, amount in u.get("creditSource", {}).items():
            if source in skip_cr_sources or amount <= 0:
                continue
            acq_type, src_cat = source_mapping.get(source, ("special", "unknown"))
            acquisition_list.append({
                "match_id": u["gameId"], "user_id": u["userNum"], "acquisition_source": source,
                "acquisition_type": acq_type, "credit_amount": float(amount), "source_category": src_cat
            })
    return pd.DataFrame(acquisition_list)

def parse_match_user_credit_expenditures(data: dict) -> pd.DataFrame:
    """
    크레딧 소모 정보 파싱 (시간 복잡도 개선)
    """
    expenditure_list = []

    # (매핑 딕셔너리들은 변경 없이 그대로 사용)
    # creditSource 내부 키 대상 매핑
    credit_source_mapping = {
        "KioskResurrection": ("revival", 1),
        "KioskRemoteDroneMySelf": ("remotedrone", 1),
        "GuideRobotSignature": ("robot", 1),
        "GuideRobotRadial": ("robot", 1),
        "guideRobotFlagShip": ("robot", 1),
    }
    
    # 키오스크(콘솔) + 안내 로봇 아이템 코드 대상 매핑 (원본 가격)
    console_item_mapping = {
        306001: ("gadget_pack", "kiosk_item", 20),
        301226: ("hamburger", "kiosk_item", 0),
        401401: ("vf_sample", "kiosk_item", 500),
        401403: ("forcecore", "kiosk_item", 350),
        401304: ("mythril", "kiosk_item", 250),
        401208: ("tree_of_life", "kiosk_item", 200),
        401209: ("meteorite", "kiosk_item", 200),
        999999: ("tactical_skill_upgrade", "kiosk_item", 200),
        502208: ("basic_drone", "robot_item", 5),
        502207: ("camera", "robot_item", 5),
    }

    # 특수 재료 총 소모량 키와 아이템 코드 매핑
    special_material_keys = {
        "crUseVFBloodSample": 401401,
        "crUseForceCore": 401403,
        "crUseMythril": 401304,
        "crUseTreeOfLife": 401208,
        "crUseMeteorite": 401209,
    }

    # 드론 아이템 코드 대상 매핑
    if data['userGames'][0]['versionSeason'] <= 8:
        fried_chicken_cr = 25
    else:
        fried_chicken_cr = 20
        
    drone_item_mapping = {
        502308: ("emp_drone", "remotedrone_item", 30),
        502208: ("basic_drone", "remotedrone_item", 20),
        502207: ("camera", "remotedrone_item", 20),
        502405: ("guillotine", "remotedrone_item", 100),
        502404: ("c4", "remotedrone_item", 100),
        301316: ("fried_chicken", "remotedrone_item", fried_chicken_cr),
    }
    
    # 로봇이 판매하는 특정 아이템의 고정 가격
    robot_fixed_prices = {
        401403: 320,
        401304: 220,
        401208: 160,
        401209: 160,
    }

    discount_trait_code = 7210801
    discount_amount = 15
    discount_target_items = {401401, 401403, 401304, 401208, 401209, 999999}

    for u in data.get("userGames", []):
        match_id = u["gameId"]
        user_id = u["userNum"]

        # (할인 로직 및 키오스크/로봇 구분 로직은 이전과 동일)
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
                    expenditure_list.append({
                        "match_id": match_id, "user_id": user_id,
                        "expenditure_item": name, "expenditure_type": exp_type,
                        "credit_amount": int(price), "usage_count": 1
                    })
                else:
                    robot_purchase_log.append(item_code)
            else:
                robot_purchase_log.append(item_code)

        # --- 로봇 구매 처리 로직 (성능 개선) ---
        remaining_items = [item for item in robot_purchase_log if item != 999999]
        # Counter를 사용해 각 아이템의 개수를 한번에 계산 (시간 복잡도 O(N))
        remaining_item_counts = Counter(remaining_items)
        
        # 이제 루프 안에서 .count()를 호출할 필요 없음
        for item_code, count in remaining_item_counts.items():
            if item_code in console_item_mapping:
                name, _, original_price = console_item_mapping[item_code]
                price = robot_fixed_prices.get(item_code, original_price)

                expenditure_list.append({
                    "match_id": match_id, "user_id": user_id,
                    "expenditure_item": name, "expenditure_type": "robot_item",
                    "credit_amount": int(count * price), "usage_count": count
                })

        # --- 기타 소모 항목 처리 ---
        credit_source = u.get("creditSource", {})
        for source_key, (exp_type, default_count) in credit_source_mapping.items():
            amount = credit_source.get(source_key, 0)
            if amount > 0:
                 expenditure_list.append({
                    "match_id": match_id, "user_id": user_id,
                    "expenditure_item": source_key, "expenditure_type": exp_type,
                    "credit_amount": int(amount), "usage_count": u.get("creditRevivalCount", 1) if source_key == "KioskResurrection" else default_count
                })

        # --- 드론 아이템 처리 로직 (성능 개선) ---
        item_transferred_drone = u.get("itemTransferredDrone", [])
        if item_transferred_drone:
            # Counter를 사용해 각 드론 아이템의 개수를 한번에 계산
            drone_item_counts = Counter(item_transferred_drone)
            
            for item_code, (name, exp_type, cost) in drone_item_mapping.items():
                # .count() 대신 O(1) 시간 복잡도의 .pop()으로 값 가져오기
                count = drone_item_counts.pop(item_code, 0)
                if count > 0:
                    expenditure_list.append({
                        "match_id": match_id, "user_id": user_id,
                        "expenditure_item": name, "expenditure_type": exp_type,
                        "credit_amount": int(count * cost), "usage_count": count
                    })
            
            # Counter에 남아있는 아이템들이 'etc'에 해당
            other_items_count = sum(drone_item_counts.values())
            if data['userGames'][0]['versionSeason'] <= 8:
                other_item_cr = 15
            else:
                other_item_cr = 10
            if other_items_count > 0:
                expenditure_list.append({
                    "match_id": match_id, "user_id": user_id,
                    "expenditure_item": "etc", "expenditure_type": "remotedrone_item",
                    "credit_amount": int(other_items_count * other_item_cr), "usage_count": other_items_count
                })
    return pd.DataFrame(expenditure_list)

def parse_match_user_stats(data: dict) -> pd.DataFrame:
    """
    유저 스탯 정보 파싱
    """
    user_stats_list = [
        {
            "match_id": u["gameId"], "user_id": u["userNum"],
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
            "match_id": u["gameId"], "user_id": u["userNum"],
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
            "match_id": u["gameId"], "user_id": u["userNum"],
            "mmr_before": u.get("mmrBefore", 0), "mmr_after": u.get("mmrAfter", 0),
            "mmr_gain": u.get("mmrGain", 0), "mmr_gain_in_game": u.get("mmrGainInGame", 0),
            "mmr_loss_entry_cost": u.get("mmrLossEntryCost", 0), "rank_point": u.get("rankPoint", 0)
        } for u in data.get("userGames", [])
    ]
    return pd.DataFrame(user_mmr_list)

def parse_object(data: dict) -> pd.DataFrame:
    """Long Format으로 오브젝트 정보 파싱"""
    object_list = []
    direct_metrics = {
        "damage_to_rumi": ("damageToGuideRobot", "damage"), "damage_to_monster": ("damageToMonster", "damage"),
        "total_kill_monster": ("monsterKill", "kill_monster"), "get_cube_red": ("getBuffCubeRed", "get_cube"),
        "get_cube_green": ("getBuffCubeGreen", "get_cube"), "get_cube_gold": ("getBuffCubeGold", "get_cube"),
        "get_cube_purple": ("getBuffCubePurple", "get_cube"), "get_cube_skyblue": ("getBuffCubeSkyBlue", "get_cube"),
    }
    kill_monster_metrics = {"8": "kill_alpha", "9": "kill_omega", "10": "kill_gamma", "7": "kill_wickline"}
    collect_log_metrics = {4: "collect_tree_of_life", 5: "collect_meteorite"}

    for u in data.get("userGames", []):
        match_id, user_id = u["gameId"], u["userNum"]
        for name, (key, mtype) in direct_metrics.items():
            if (value := u.get(key, 0)) > 0:
                object_list.append({"match_id": match_id, "user_id": user_id, "metric_type": mtype, "metric_name": name, "value": value})
        for key, name in kill_monster_metrics.items():
            value = u.get("killMonsters", {}).get(key, 0)
            if name == "kill_wickline": value = 1 if value > 0 else 0
            if value > 0:
                object_list.append({"match_id": match_id, "user_id": user_id, "metric_type": "kill_boss", "metric_name": name, "value": value})
        collect_log = u.get("collectItemForLog", [])
        for idx, name in collect_log_metrics.items():
            if len(collect_log) > idx and (value := collect_log[idx]) > 0:
                object_list.append({"match_id": match_id, "user_id": user_id, "metric_type": "collect_special", "metric_name": name, "value": value})
        for key, value in u.get("activeInstallation", {}).items():
            if value > 0:
                object_list.append({"match_id": match_id, "user_id": user_id, "metric_type": "installation", "metric_name": int(key), "value": value})
    return pd.DataFrame(object_list)

def parse_match_user_credit_time(data: dict) -> pd.DataFrame:
    """분당 크레딧 정보 파싱"""
    user_credit_time_list = []
    for u in data.get("userGames", []):
        for minute in range(20):
            used = u["usedVFCredits"][minute]
            gain = u["totalVFCredits"][minute]
            if used != 0 or gain != 0:
                user_credit_time_list.append({"match_id": u["gameId"], "user_id": u["userNum"], "minute": minute, "used_credit": used, "gain_credit": gain})
    return pd.DataFrame(user_credit_time_list)

def parse_match_user_sight(data: dict) -> pd.DataFrame:
    """시야 정보 파싱"""
    user_sight_list = [
        {
            "match_id": u["gameId"], "user_id": u["userNum"],
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
        return {
            "match_info": parse_match_info(data),
            "match_team_info": parse_match_team_info(data),
            "match_user_start": parse_match_user_start(data),
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
    except Exception as e:
        print(f"Error parsing match data: {e}")
        raise