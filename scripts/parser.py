import json
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional


def top_ranker_id(data: dict) -> dict:
    """
    아시아 지역 1000위 이상 유저의 User Id를 파싱하는 함수
    """
    top_1000_users = []
    for i in range(len(data['topRanks'])):
        top_1000_users.append(data['topRanks'][i]['userNum'])
    return top_1000_users

def parse_match_info(data: dict) -> dict:
    """
    Parse basic match information from the JSON data.
    Returns a dictionary with match_info table data.
    """
    if not data.get("userGames") or len(data["userGames"]) == 0:
        raise ValueError("No user games data found in the input")
    
    # Using first user data to get match info
    user_json = data["userGames"][0]
    match_info = {
        "match_id": user_json["gameId"],
        "start_dtm": user_json["startDtm"],
        "match_mode": user_json["matchingTeamMode"],
        "season_id": user_json["seasonId"],
        "version_major": user_json["versionMajor"],
        "version_minor": user_json["versionMinor"],
        "weather_main": user_json["mainWeather"],
        "weather_sub": user_json["subWeather"],
        "match_size": len(data["userGames"]),
        "match_avg_mmr": user_json["mmrAvg"],
        # Find match end time from the winner (rank 1)
        "match_end": next((u["expireDtm"] for u in data["userGames"] if u["gameRank"] == 1), None)
    }
    
    return match_info

def parse_match_team_info(data: dict) -> List[dict]:
    """
    Parse team information from the JSON data.
    Returns a list of dictionaries with match_team_info table data.
    """
    team_info_list = []
    processed_team_ids = set()
    
    for user_json in data.get("userGames", []):
        team_id = user_json["teamNumber"]
        
        # Skip if this team has already been processed
        if team_id in processed_team_ids:
            continue
        
        match_id = user_json["gameId"]
        start_dtm = user_json["startDtm"]
        start_dtm = datetime.strptime(start_dtm, "%Y-%m-%dT%H:%M:%S.%f%z")
        
        expire_dtm = user_json["expireDtm"]
        expire_dtm = datetime.strptime(expire_dtm, "%Y-%m-%dT%H:%M:%S.%f%z")
        
        is_older_version = user_json["versionMajor"] <= 44
        
        team_info = {
            "match_id": match_id,
            "team_id": team_id,
            "team_ranking": user_json["gameRank"],
            "escape_state": user_json["escapeState"],
            "expire_dtm": expire_dtm, # 2025-04-21T03:45:34.034+0900
            "player_down": user_json["teamDown"],
            "total_play_time": expire_dtm - start_dtm,
            "team_elimination_count": user_json["teamElimination"]
        }
        
        # Version-specific field mapping
        if is_older_version:
            team_info.update({
                "team_down_in_auto_reserrection": user_json["teamDownInAutoResurrection"],
                "team_down_after_auto_reserrection": user_json["teamDownDeactiveAutoResurrection"],
                "team_repeat_down_in_auto_reserrection": user_json["teamRepeatDownInAutoResurrection"],
                "team_repeat_down_after_auto_reserrection": user_json["teamRepeatDownDeactiveAutoResurrection"]
            })
        else:
            team_info.update({
                "team_down_in_auto_reserrection": user_json["teamDownCanNotEliminate"],
                "team_down_after_auto_reserrection": user_json["teamDownCanEliminate"],
                "team_repeat_down_in_auto_reserrection": user_json["teamRepeatDownCanNotEliminate"],
                "team_repeat_down_after_auto_reserrection": user_json["teamRepeatDownCanEliminate"]
            })
        
        team_info_list.append(team_info)
        processed_team_ids.add(team_id)
    
    return team_info_list

def parse_match_user_basic(data: dict) -> List[dict]:
    """
    Parse basic user match information from the JSON data.
    Returns a list of dictionaries with match_user_basic table data.
    """
    user_basic_list = []
    
    for user_json in data.get("userGames", []):
        user_basic = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "team_id": user_json["teamNumber"],
            "except_premade_team": user_json["exceptPreMadeTeam"],
            "character_id": user_json["characterNum"],
            "skin_id": user_json["skinCode"],
            "character_level": user_json["characterLevel"],
            "total_kill": user_json["playerKill"],
            "total_death": user_json["playerDeaths"],
            "total_assist": user_json["playerAssistant"],
            "weapon_type": user_json["bestWeapon"],
            "weapon_level": user_json["bestWeaponLevel"],
            "play_time": user_json["playTime"],
            "watch_time": user_json["watchTime"],
            "total_damage_to_player": user_json["damageToPlayer"],
            "total_damage_from_player": user_json["damageFromPlayer"],
            "total_heal": user_json["healAmount"],
            "heal_to_team": user_json["teamRecover"],
            "use_loop_count": user_json["useHyperLoop"],
            "user_security_console_count": user_json["useSecurityConsole"],
            "route_id": user_json["routeIdOfStart"],
            "start_place": int(user_json["placeOfStart"]),
            "emotion_count": user_json["useEmoticonCount"],
            "fishing_count": user_json["fishingCount"],
            "tactical_skill_id": user_json["tacticalSkillGroup"],
            "tactical_skill_level": user_json["tacticalSkillLevel"],
            "tactical_skill_count": user_json["tacticalSkillUseCount"],
            "credit_revival_count": user_json["creditRevivalCount"],
            "credit_revival_other_count": user_json["creditRevivedOthersCount"],
            "user_end_time": datetime.strptime(user_json["expireDtm"], "%Y-%m-%dT%H:%M:%S.%f%z")
        }
        
        user_basic_list.append(user_basic)
    
    return user_basic_list

def parse_match_user_equipment(data: dict) -> List[dict]:
    """
    Parse user equipment information from the JSON data.
    Returns a list of dictionaries with match_user_equipment table data.
    """
    user_equipment_list = []
    
    for user_json in data.get("userGames", []):
        equipment = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "equipment_weapon": user_json["equipment"].get("0"),
            "equipment_chest": user_json["equipment"].get("1"),
            "equipment_head": user_json["equipment"].get("2"),
            "equipment_arm": user_json["equipment"].get("3"),
            "equipment_leg": user_json["equipment"].get("4"),
            "first_equipment_weapon": user_json["equipFirstItemForLog"]["0"][-1],
            "first_equipment_chest": user_json["equipFirstItemForLog"]["1"][-1],
            "first_equipment_head": user_json["equipFirstItemForLog"]["2"][-1],
            "first_equipment_arm": user_json["equipFirstItemForLog"]["3"][-1],
            "first_equipment_leg": user_json["equipFirstItemForLog"]["4"][-1]
        }
        
        user_equipment_list.append(equipment)
    
    return user_equipment_list

def parse_match_user_stat(data: dict) -> List[dict]:
    """
    Parse user stats information from the JSON data.
    Returns a list of dictionaries with match_user_stat table data.
    """
    user_stat_list = []
    
    for user_json in data.get("userGames", []):
        user_stat = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "hp": user_json["maxHp"],
            "sp": user_json["maxSp"],
            "hp_regen": user_json["hpRegen"],
            "sp_regen": user_json["spRegen"],
            "depense": user_json["defense"],
            "attack_power": user_json["attackPower"],
            "attack_speed": user_json["attackSpeed"],
            "skill_amp": user_json["skillAmp"],
            "cooldown_percent": float(user_json["coolDownReduction"]),
            "adaptive_force": user_json["adaptiveForce"],
            "adaptive_force_attack": user_json["adaptiveForceAttack"],
            "adaptive_force_amp": user_json["adaptiveForceAmplify"],
            "move_speed": float(user_json["moveSpeed"]),
            "ooc_move_speed": float(user_json["outOfCombatMoveSpeed"]),
            "sight_range": float(user_json["sightRange"]),
            "attack_range": float(user_json["attackRange"]),
            "critical_percent": user_json["criticalStrikeChance"],
            "critical_damage": user_json["criticalStrikeDamage"],
            "life_steal_percent": float(user_json["lifeSteal"]),
            "normal_life_steel": int(user_json["normalLifeSteal"] * 100),
            "skill_life_steel": user_json["skillLifeSteal"]
        }
        
        user_stat_list.append(user_stat)
    
    return user_stat_list

def parse_match_user_damage(data: dict) -> List[dict]:
    """
    Parse user damage information from the JSON data.
    Returns a list of dictionaries with match_user_damage table data.
    """
    user_damage_list = []
    
    for user_json in data.get("userGames", []):
        user_damage = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "basic_damage_to_player": user_json["damageToPlayer_basic"],
            "skill_damage_to_player": user_json["damageToPlayer_skill"],
            "direct_damage_to_player": user_json["damageToPlayer_direct"],
            "shield_damage_to_player": user_json["damageToPlayer_Shield"],
            "item_damage_to_player": user_json["damageToPlayer_itemSkill"],
            "trap_damage_to_player": user_json["damageToPlayer_trap"],
            "basic_damage_from_player": user_json["damageFromPlayer_basic"],
            "skill_damage_from_player": user_json["damageFromPlayer_skill"],
            "direct_damage_from_player": user_json["damageFromPlayer_direct"],
            "shield_damage_from_player": user_json["damageOffsetedByShield_Player"],
            "item_damage_from_player": user_json["damageFromPlayer_itemSkill"],
            "trap_damage_from_player": user_json["damageFromPlayer_trap"]
        }
        
        user_damage_list.append(user_damage)
    
    return user_damage_list

def parse_match_user_trait(data: dict) -> List[dict]:
    """
    Parse user trait information from the JSON data.
    Returns a list of dictionaries with match_user_trait table data.
    """
    user_trait_list = []
    
    for user_json in data.get("userGames", []):
        user_trait = {
            "user_id": user_json["userNum"],
            "match_id": user_json["gameId"],
            "core_trait_id": user_json["traitFirstCore"],
            "first_trait_id1": user_json["traitFirstSub"][0],
            "first_trait_id2": user_json["traitFirstSub"][1],
            "second_trait_id1": user_json["traitSecondSub"][0],
            "second_trait_id2": user_json["traitSecondSub"][1]
        }
        
        user_trait_list.append(user_trait)
    
    return user_trait_list

def parse_match_user_mmr(data: dict) -> List[dict]:
    """
    Parse user MMR information from the JSON data.
    Returns a list of dictionaries with match_user_mmr table data.
    """
    user_mmr_list = []
    
    for user_json in data.get("userGames", []):
        user_mmr = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "before_mmr": user_json["mmrBefore"],
            "after_mmr": user_json["mmrAfter"],
            "mmr_gain": user_json["mmrGain"],
            "mmr_entry_loss": user_json["mmrLossEntryCost"]
        }
        
        user_mmr_list.append(user_mmr)
    
    return user_mmr_list

def parse_user_match_kda_detail(data: dict) -> List[dict]:
    """
    Parse user KDA detail information from the JSON data.
    Returns a list of dictionaries with user_match_kda_detail table data.
    """
    user_kda_list = []
    
    for user_json in data.get("userGames", []):
        user_kda = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "kill_phase_one": user_json["killsPhaseOne"],
            "kill_phase_two": user_json["killsPhaseTwo"],
            "kill_phase_three": user_json["killsPhaseThree"],
            "death_phase_one": user_json["deathsPhaseOne"],
            "death_phase_two": user_json["deathsPhaseTwo"],
            "death_phase_three": user_json["deathsPhaseThree"]
        }
        
        user_kda_list.append(user_kda)
    
    return user_kda_list

def parse_match_user_sight(data: dict) -> List[dict]:
    """
    Parse user sight information from the JSON data.
    Returns a list of dictionaries with match_user_sight table data.
    """
    user_sight_list = []
    
    for user_json in data.get("userGames", []):
        user_sight = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "sight_score": user_json["viewContribution"],
            "camera_setup": user_json["addTelephotoCamera"],
            "camera_remove": user_json["removeTelephotoCamera"],
            "emp_drone_setup": user_json["useEmpDrone"],
            "basic_drone_setup": user_json["useReconDrone"]
        }
        
        user_sight_list.append(user_sight)
    
    return user_sight_list

def parse_object(data: dict) -> List[dict]:
    """
    Parse object information from the JSON data.
    Returns a list of dictionaries with object table data.
    """
    object_list = []
    
    for user_json in data.get("userGames", []):
        kill_monsters = user_json.get("killMonsters", {})
        
        object_data = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "damage_to_rumi": user_json["damageToGuideRobot"],
            "damage_to_monster": user_json["damageToMonster"],
            "total_kill_monster": user_json["monsterKill"],
            "kill_alpha": kill_monsters.get("8", 0),
            "kill_omega": kill_monsters.get("9", 0),
            "kill_gamma": kill_monsters.get("10", 0),
            "kill_wickline": 1 if kill_monsters.get("7", 0) > 0 else 0,
            "get_cube_red": user_json["getBuffCubeRed"],
            "get_cube_green": user_json["getBuffCubeGreen"],
            "get_cube_gold": user_json["getBuffCubeGold"],
            "get_cube_purple": user_json["getBuffCubePurple"],
            "get_cube_skyblue": user_json["getBuffCubeSkyBlue"],
            "collect_tree_of_life": user_json["collectItemForLog"][4],
            "collect_meteorite": user_json["collectItemForLog"][5],
            "get_air_supply_purple": user_json["airSupplyOpenCount"][3],
            "get_air_supply_red": user_json["airSupplyOpenCount"][5]
        }
        
        object_list.append(object_data)
    
    return object_list

def parse_match_user_gain_credit(data: dict) -> List[dict]:
    """
    Parse user credit gain information from the JSON data.
    Returns a list of dictionaries with match_user_gain_credit table data.
    """
    user_gain_credit_list = []
    
    for user_json in data.get("userGames", []):
        credit_source = user_json.get("creditSource", {})
        
        gain_credit = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "total_gain_cr": user_json["totalGainVFCredit"],
            "start_cr": credit_source["PreliminaryPhase"],
            "time_elapse_cr": credit_source["TimeElapsedCompensationByMiliSecond"],
            "time_elapse_bonus_cr": int(credit_source.get("TimeElapsedCreditBonusByMiliSecond",0)),
            "wild_dog_cr": credit_source.get("KillWildDog", 0),
            "bat_cr": credit_source.get("KillBat", 0),
            "chicken_cr": credit_source.get("KillChicken", 0),
            "boar_cr": credit_source.get("KillBoar", 0),
            "wolf_cr": credit_source.get("KillWolf", 0),
            "bear_cr": credit_source.get("KillBear", 0),
            "raven_cr": credit_source.get("KillRaven", 0),
            "mutant_wild_dog_cr": credit_source.get("KillMutantWildDog", 0),
            "mutant_bat_cr": credit_source.get("KillMutantBat", 0),
            "mutant_chicken_cr": credit_source.get("KillMutantChicken", 0),
            "mutant_boar_cr": credit_source.get("KillMutantBoar", 0),
            "mutant_wolf_cr": credit_source.get("KillMutantWolf", 0),
            "mutant_bear_cr": credit_source.get("KillMutantBear", 0),
            "mutant_raven_cr": credit_source.get("KillMutantRaven", 0),
            "alpha_cr": credit_source.get("KillAlpha",0),
            "omega_cr": credit_source.get("KillOmega",0),
            "gamma_cr": credit_source.get("KillGamma", 0),
            "wickline_cr": credit_source.get("KillWickline", 0),
            "security_console_cr": credit_source.get("GoldSecurityConsoleAccess",0),
            "drone_cr": credit_source.get("KillDrone", 0),
            "kill_cr": user_json["crGetKill"],
            "kill_by_team_cr": credit_source.get("KillAssistDivideContribute",0),
            "rumi_cr": user_json["crGetByGuideRobot"],
            "skill_cr": credit_source.get("GetBySkill", 0),
            "cointoss_cr": credit_source.get("TraitSkillCoinToss", 0),
            "item_bounty_cr": credit_source.get("ItemBountyByItemCode", 0),
            "kill_bounty_cr": credit_source.get("ItemBounty", 0),
            "door_console_cr": credit_source.get("DoorConsoleAccess",0)
        }
        
        user_gain_credit_list.append(gain_credit)
    
    return user_gain_credit_list

def parse_match_user_use_credit(data: dict) -> List[dict]:
    """
    Parse user credit usage information from the JSON data.
    Returns a list of dictionaries with match_user_use_credit table data.
    """
    user_use_credit_list = []
    
    for user_json in data.get("userGames", []):
        credit_source = user_json.get("creditSource", {})
        item_transferred = user_json.get("itemTransferredDrone", [])
        
        use_credit = {
            "match_id": user_json["gameId"],
            "user_id": user_json["userNum"],
            "total_used_cr": user_json["totalUseVFCredit"],
            "used_revival_cr": user_json["transferConsoleFromRevivalUseVFCredit"],
            "used_remote_drone_myself_cr": user_json["remoteDroneUseVFCreditMySelf"],
            "used_remote_drone_myteam_cr": user_json["remoteDroneUseVFCreditAlly"],
            "used_tactical_skill_cr": user_json["crUseUpgradeTacticalSkill"],
            "used_tree_of_life_cr": user_json["crUseTreeOfLife"],
            "used_meteorite_cr": user_json["crUseMeteorite"],
            "used_mythril_cr": user_json["crUseMythril"],
            "used_forcecore_cr": user_json["crUseForceCore"],
            "used_blood_sample_cr": user_json["crUseVFBloodSample"],
            "used_escapekit_cr": user_json["crUseRootkit"],
            "used_emp_drone_cr": item_transferred.count(502308) * 30,
            "used_basic_drone_cr": item_transferred.count(502208) * 20,
            "used_camera_cr": item_transferred.count(502207) * 20,
            "used_guillotine_cr": item_transferred.count(502405) * 100,
            "used_c4_cr": item_transferred.count(502404) * 100,
            "used_fried_chicken_cr": item_transferred.count(301316) * 25,
            "used_rumi_signiture_cr": credit_source.get("GuideRobotSignature", 0),
            "used_rumi_fragship_cr": credit_source.get("guideRobotFlagShip", 0),
            "used_rumi_radial_cr": credit_source.get("GuideRobotRadial", 0)
        }
        
        user_use_credit_list.append(use_credit)
    
    return user_use_credit_list

def parse_match_user_credit_time(data: dict) -> List[dict]:
    """
    Parse user credit time information from the JSON data.
    Returns a list of dictionaries with match_user_credit_time table data.
    """
    user_credit_time_list = []
    
    for user_json in data.get("userGames", []):
        match_id = user_json["gameId"]
        user_id = user_json["userNum"]
        
        for minute in range(20):  # 20 minutes maximum
            used_credit = user_json["usedVFCredits"][minute]
            gain_credit = user_json["totalVFCredits"][minute]
            
            # Only add entries where there's credit activity
            if used_credit != 0 or gain_credit != 0:
                user_credit_time = {
                    "match_id": match_id,
                    "user_id": user_id,
                    "minute": minute,
                    "used_credit": used_credit,
                    "gain_credit": gain_credit
                }
                
                user_credit_time_list.append(user_credit_time)
    
    return user_credit_time_list

def parse_match_data(data: dict) -> Dict[str, Any]:
    """
    Main function to parse all match data from the JSON input.
    Returns a dictionary containing all parsed tables.
    """
    try:
        result = {
            "match_info": parse_match_info(data),
            "match_team_info": parse_match_team_info(data),
            "match_user_basic": parse_match_user_basic(data),
            "match_user_equipment": parse_match_user_equipment(data),
            "match_user_stat": parse_match_user_stat(data),
            "match_user_damage": parse_match_user_damage(data),
            "match_user_trait": parse_match_user_trait(data),
            "match_user_mmr": parse_match_user_mmr(data),
            "user_match_kda_detail": parse_user_match_kda_detail(data),
            "match_user_sight": parse_match_user_sight(data),
            "object": parse_object(data),
            "match_user_gain_credit": parse_match_user_gain_credit(data),
            "match_user_use_credit": parse_match_user_use_credit(data),
            "match_user_credit_time": parse_match_user_credit_time(data)
        }
        
        return result
    except Exception as e:
        print(f"Error parsing match data: {e}")
        raise