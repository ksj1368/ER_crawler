from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Float, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

# Alembic이 이 메타데이터를 보고 DB 변경을 감지
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    uid = Column(String(128), primary_key=True, comment='User Identifier')
    nickname = Column(String(30), index=True)
    last_match_id = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AreaInfo(Base):
    __tablename__ = 'area_info'
    area_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    area_name = Column(String(32))

class CharacterInfo(Base):
    __tablename__ = 'character_info'
    character_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    character_name = Column(String(32))
    archetype_primary = Column(String(32))
    archetype_secondary = Column(String(32))
    weapon_range_type = Column(String(32))
    base_max_hp = Column(Integer)
    base_attack_power = Column(Integer)
    base_defense = Column(Integer)
    base_skill_amp = Column(Integer)
    base_hp_regen = Column(Float)
    base_attack_speed = Column(Float)
    base_move_speed = Column(Float)
    base_sight_range = Column(Float)

class CharacterLevelupStats(Base):
    __tablename__ = 'character_levelup_stats'
    character_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    levelup_max_hp = Column(Float)
    levelup_attack_power = Column(Float)
    levelup_defense = Column(Float)
    levelup_hp_regen = Column(Float)

class InstallationInfo(Base):
    __tablename__ = 'installation_info'
    installation_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    installation_name = Column(String(32))

class ItemArmor(Base):
    __tablename__ = 'item_armor'
    item_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    item_name = Column(String(32))
    item_type = Column(String(16))
    armor_type = Column(String(16))
    item_grade = Column(String(16))
    manufacturable_type = Column(Integer)
    attack_power = Column(Integer)
    defense = Column(Integer)
    skill_amp = Column(Integer)
    max_hp = Column(Integer)
    hp_regen = Column(Integer)
    attack_speed_ratio = Column(Integer)
    critical_strike_chance = Column(Integer)
    critical_strike_damage = Column(Integer)
    cooldown_reduction = Column(Integer)
    life_steal = Column(Integer)
    move_speed = Column(Float)
    move_speed_ratio = Column(Float)

class ItemWeapon(Base):
    __tablename__ = 'item_weapon'
    item_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    item_name = Column(String(32))
    weapon_type = Column(String(16))
    item_grade = Column(String(16))
    manufacturable_type = Column(Integer)
    attack_power = Column(Integer)
    defense = Column(Integer)
    skill_amp = Column(Integer)
    max_hp = Column(Integer)
    attack_speed_ratio = Column(Integer)
    critical_strike_chance = Column(Integer)
    critical_strike_damage = Column(Integer)
    cooldown_reduction = Column(Integer)
    life_steal = Column(Integer)
    attack_range = Column(Float)

class MonsterInfo(Base):
    __tablename__ = 'monster_info'
    monster_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    monster_name = Column(String(32))
    monster_grade = Column(String(16))
    is_mutant = Column(Boolean)
    max_hp = Column(Integer)
    attack_power = Column(Integer)
    defense = Column(Integer)
    attack_speed = Column(Float)
    move_speed = Column(Float)
    attack_range = Column(Float)
    sight_range = Column(Integer)
    gain_exp = Column(Integer)

class TraitInfo(Base):
    __tablename__ = 'trait_info'
    trait_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    trait_name = Column(String(32))

class WeatherInfo(Base):
    __tablename__ = 'weather_info'
    weather_id = Column(Integer, primary_key=True)
    season = Column(Integer, primary_key=True)
    major_version = Column(Integer, primary_key=True)
    minor_version = Column(Integer, primary_key=True)
    weather_name = Column(String(16))

# --- Manually Managed Tables ---

class ArmorTypes(Base):
    __tablename__ = 'armor_types'
    armor_id = Column(Integer, primary_key=True)
    armor_name = Column(String(32), unique=True)

class WeaponTypes(Base):
    __tablename__ = 'weapon_types'
    weapon_id = Column(Integer, primary_key=True)
    weapon_name = Column(String(32), unique=True)

class TacticalSkills(Base):
    __tablename__ = 'tactical_skills'
    tactical_skill_id = Column(Integer, primary_key=True)
    tactical_skill_name = Column(String(16), unique=True)

# --- Match Data Tables ---

class MatchInfo(Base):
    __tablename__ = 'match_info'
    match_id = Column(Integer, primary_key=True)
    season_id = Column(Integer)
    version_season = Column(Integer)
    version_major = Column(Integer)
    version_minor = Column(Integer)
    matching_mode = Column(Integer)
    matching_team_mode = Column(Integer)
    server_name = Column(String(32))
    match_size = Column(Integer)
    start_dtm = Column(DateTime)
    duration = Column(Integer)
    expired_tm = Column(DateTime)
    mmr_avg = Column(Integer)
    main_weather = Column(Integer)
    sub_weather = Column(Integer)
    bot_added = Column(Integer)
    bot_remain = Column(Integer)
    safe_areas = Column(Integer)
    restricted_area_accelerated = Column(Integer)

    teams = relationship("MatchTeamInfo", back_populates="match")

class MatchTeamInfo(Base):
    __tablename__ = 'match_team_info'
    match_id = Column(Integer, ForeignKey('match_info.match_id'), primary_key=True)
    team_number = Column(Integer, primary_key=True)
    game_rank = Column(Integer)
    team_kill = Column(Integer)
    total_field_kill = Column(Integer)
    team_elimination = Column(Integer)
    team_down = Column(Integer)
    team_repeat_down = Column(Integer)
    team_battle_zone_down = Column(Integer)
    escape_state = Column(Integer)
    team_down_cannot_eliminate = Column(Integer)
    team_down_can_eliminate = Column(Integer)
    team_repeat_down_cannot_eliminate = Column(Integer)
    team_repeat_down_can_eliminate = Column(Integer)

    match = relationship("MatchInfo", back_populates="teams")
    users = relationship("MatchUserStart", back_populates="team")

class MatchUserStart(Base):
    __tablename__ = 'match_user_start'
    match_id = Column(Integer, ForeignKey('match_team_info.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('user.uid'), primary_key=True)
    nickname = Column(String(32))
    character_num = Column(Integer)
    language = Column(String(32))
    team_number = Column(Integer)
    skin_code = Column(Integer)
    premade = Column(Integer)
    except_premade_team = Column(Integer)
    route_id_of_start = Column(Integer)
    place_of_start = Column(Integer)
    using_default_game_option = Column(Boolean)
    premade_matching_type = Column(Integer)
    tactical_skill_id = Column(Integer)
    ml_bot = Column(Boolean)

    team = relationship("MatchTeamInfo", back_populates="users")

class MatchUserEnd(Base):
    __tablename__ = 'match_user_end'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    victory = Column(Boolean)
    play_time = Column(Integer)
    watch_time = Column(Integer)
    total_time = Column(Integer)
    time_spent_in_briefing_room = Column(Integer)
    craft_uncommon = Column(Integer)
    craft_rare = Column(Integer)
    craft_epic = Column(Integer)
    craft_legend = Column(Integer)
    craft_mythic = Column(Integer)
    use_hyperloop = Column(Integer)
    use_security_console = Column(Integer)
    break_count = Column(Integer)
    enter_dimension_rift = Column(Integer)
    enter_dimension_empowered_rift = Column(Integer)
    win_dimension_rift = Column(Integer)
    win_dimension_empowered_rift = Column(Integer)
    resurrectionkit_count = Column(Integer)
    resurrectionkit_credit_count = Column(Integer)
    fishing_count = Column(Integer)
    emoticon_count = Column(Integer)
    used_pairloop = Column(Integer)
    give_up = Column(Integer)
    team_spectator = Column(Integer)
    is_leaving_before_credit_revival_terminate = Column(Boolean)

class MatchUserCombat(Base):
    __tablename__ = 'match_user_combat'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    character_level = Column(Integer)
    tactical_skill_level = Column(Integer)
    player_kill = Column(Integer)
    player_assistant = Column(Integer)
    player_deaths = Column(Integer)
    monster_kill = Column(Integer)
    kills_phase_one = Column(Integer)
    kills_phase_two = Column(Integer)
    kills_phase_three = Column(Integer)
    deaths_phase_one = Column(Integer)
    deaths_phase_two = Column(Integer)
    deaths_phase_three = Column(Integer)
    terminate_count = Column(Integer)
    terminate_count_cannot_eliminate = Column(Integer)
    clutch_count = Column(Integer)
    unknown_kill = Column(Integer)
    cc_time_to_player = Column(Float)
    credit_revival_count = Column(Integer)
    credit_revived_others_count = Column(Integer)
    reunited_count = Column(Integer)
    tactical_skill_count = Column(Integer)

class MatchUserTrait(Base):
    __tablename__ = 'match_user_trait'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    trait_id = Column(Integer, primary_key=True)
    trait_type = Column(String(16))

class MatchUserDamage(Base):
    __tablename__ = 'match_user_damage'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    damage_to_player_total = Column(Integer)
    damage_to_player_basic = Column(Integer)
    damage_to_player_skill = Column(Integer)
    damage_to_player_item_skill = Column(Integer)
    damage_to_player_direct = Column(Integer)
    damage_to_player_trap = Column(Integer)
    damage_to_player_unique_skill = Column(Integer)
    damage_to_player_shield = Column(Integer)
    damage_from_player_total = Column(Integer)
    damage_from_player_basic = Column(Integer)
    damage_from_player_skill = Column(Integer)
    damage_from_player_item_skill = Column(Integer)
    damage_from_player_direct = Column(Integer)
    damage_from_player_trap = Column(Integer)
    damage_from_player_unique_skill = Column(Integer)
    damage_to_monster_total = Column(Integer)
    damage_to_monster_basic = Column(Integer)
    damage_to_monster_skill = Column(Integer)
    damage_to_monster_item_skill = Column(Integer)
    damage_to_monster_direct = Column(Integer)
    damage_to_monster_trap = Column(Integer)
    damage_to_monster_unique_skill = Column(Integer)
    damage_from_monster_total = Column(Integer)
    damage_offseted_by_shield_player = Column(Integer)
    damage_offseted_by_shield_monster = Column(Integer)
    damage_to_guide_robot = Column(Integer)
    heal_amount = Column(Integer)
    team_recover = Column(Integer)
    protect_absorb = Column(Integer)

class MatchUserEquipment(Base):
    __tablename__ = 'match_user_equipment'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    first_weapon = Column(Integer)
    first_chest = Column(Integer)
    first_head = Column(Integer)
    first_arm = Column(Integer)
    first_leg = Column(Integer)
    last_weapon = Column(Integer)
    last_chest = Column(Integer)
    last_head = Column(Integer)
    last_arm = Column(Integer)
    last_leg = Column(Integer)
    best_weapon = Column(Integer)
    best_weapon_level = Column(Integer)

class MatchUserStats(Base):
    __tablename__ = 'match_user_stats'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    max_hp = Column(Integer)
    hp_regen = Column(Float)
    attack_power = Column(Integer)
    attack_speed = Column(Float)
    defense = Column(Integer)
    skill_amp = Column(Integer)
    move_speed = Column(Float)
    ooc_move_speed = Column(Float)
    sight_range = Column(Integer)
    attack_range = Column(Float)
    adaptive_force = Column(Float)
    adaptive_force_attack = Column(Float)
    adaptive_force_amp = Column(Float)
    critical_strike_chance = Column(Float)
    critical_damage = Column(Integer)
    cooldown_reduction = Column(Integer)
    life_steal = Column(Integer)
    normal_life_steal = Column(Integer)
    skill_life_steal = Column(Integer)

class MatchUserMmr(Base):
    __tablename__ = 'match_user_mmr'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    mmr_before = Column(Integer)
    mmr_after = Column(Integer)
    mmr_gain = Column(Integer)
    mmr_gain_in_game = Column(Integer)
    mmr_loss_entry_cost = Column(Integer)
    rank_point = Column(Integer)

class MatchUserSight(Base):
    __tablename__ = 'match_user_sight'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    sight_score = Column(Integer)
    camera_setup = Column(Integer)
    camera_remove = Column(Integer)
    emp_drone_setup = Column(Integer)
    basic_drone_setup = Column(Integer)

# --- Long Format Data Tables ---

class MatchUserCreditAcquisitions(Base):
    __tablename__ = 'match_user_credit_acquisitions'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    acquisition_source = Column(String(32), primary_key=True)
    acquisition_type = Column(String(32))
    credit_amount = Column(Float)
    source_category = Column(String(32))

class MatchUserCreditExpenditures(Base):
    __tablename__ = 'match_user_credit_expenditures'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    expenditure_item = Column(String(32), primary_key=True)
    expenditure_type = Column(String(32))
    credit_amount = Column(Integer)
    usage_count = Column(Integer)

class MatchUserCreditTime(Base):
    __tablename__ = 'match_user_credit_time'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    minute = Column(Integer, primary_key=True)
    used_credit = Column(Integer)
    gain_credit = Column(Integer)

class MatchUserObject(Base):
    __tablename__ = 'match_user_object'
    match_id = Column(Integer, ForeignKey('match_user_start.match_id'), primary_key=True)
    uid = Column(String(128), ForeignKey('match_user_start.uid'), primary_key=True)
    metric_type = Column(String(32))
    metric_name = Column(String(32), primary_key=True)
    value = Column(Integer)
