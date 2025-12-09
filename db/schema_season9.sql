/*
 * =================================================================================
 * 이터널 리턴 데이터 분석용 DB 스키마 (v2.1 Refactored)
 * ---------------------------------------------------------------------------------
 * 변경 내역:
 * 1. `uid` 컬럼 타입을 TEXT에서 VARCHAR(32)로 변경하여 인덱싱 성능 및 저장 효율 개선.
 * =================================================================================
 */

-- =================================================================================
-- 1. 메타 정보 테이블 (버전별 데이터)
-- =================================================================================

-- 수집이 끝나면 갱신
CREATE TABLE user (
    uid VARCHAR(128) NOT NULL PRIMARY KEY,
    nickname VARCHAR(30),
    last_match_id BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    last_updated_at DATETIME
);

CREATE TABLE area_info (
  area_id INT COMMENT '원본 JSON 키: code',
  season INT,
  major_version INT,
  minor_version INT,
  area_name VARCHAR(255) COMMENT '원본 JSON 키: name',
  UNIQUE KEY uq_area_version (area_id, season, major_version, minor_version)
) COMMENT '지역 정보';

CREATE TABLE character_info (  
  character_id INT COMMENT '원본 JSON 키: code',
  season INT,
  major_version INT,
  minor_version INT,
  character_name VARCHAR(255) COMMENT '원본 JSON 키: name',
  archetype_primary VARCHAR(255) COMMENT '원본 JSON 키: charArcheType1',
  archetype_secondary VARCHAR(255) COMMENT '원본 JSON 키: charArcheType2',
  weapon_range_type VARCHAR(255) COMMENT '원본 JSON 키: weaponRangeType',
  base_max_hp INT COMMENT '원본 JSON 키: maxHp',
  base_attack_power INT COMMENT '원본 JSON 키: attackPower',
  base_defense INT COMMENT '원본 JSON 키: defense',
  base_skill_amp INT COMMENT '원본 JSON 키: skillAmp',
  base_hp_regen FLOAT COMMENT '원본 JSON 키: hpRegen',
  base_attack_speed FLOAT COMMENT '원본 JSON 키: attackSpeed',
  base_move_speed FLOAT COMMENT '원본 JSON 키: moveSpeed',
  base_sight_range FLOAT COMMENT '원본 JSON 키: sightRange',
  UNIQUE KEY uq_character_version (character_id, season, major_version, minor_version)
) COMMENT '캐릭터 기본 정보';

CREATE TABLE character_levelup_stats (
  character_id INT COMMENT '원본 JSON 키: code',
  season INT,
  major_version INT,
  minor_version INT,
  levelup_max_hp FLOAT COMMENT '원본 JSON 키: maxHp',
  levelup_attack_power FLOAT COMMENT '원본 JSON 키: attackPower',
  levelup_defense FLOAT COMMENT '원본 JSON 키: defense',
  levelup_hp_regen FLOAT COMMENT '원본 JSON 키: hpRegen',
  UNIQUE KEY uq_char_levelup_version (character_id, season, major_version, minor_version)
) COMMENT '캐릭터 레벨업 스탯';

CREATE TABLE installation_info (
  installation_id INT COMMENT 'l10n 파싱 데이터',
  season INT,
  major_version INT,
  minor_version INT,
  installation_name VARCHAR(255) COMMENT 'l10n 파싱 데이터',
  UNIQUE KEY uq_installation_version (installation_id, season, major_version, minor_version)
) COMMENT '설치물 정보';

CREATE TABLE item_armor (
  item_id INT COMMENT '원본 JSON 키: code',
  item_name VARCHAR(255) COMMENT '원본 JSON 키: name',
  season INT,
  major_version INT,
  minor_version INT,
  item_type VARCHAR(255) COMMENT '원본 JSON 키: itemType',
  armor_type VARCHAR(255) COMMENT '원본 JSON 키: armorType',
  item_grade VARCHAR(255) COMMENT '원본 JSON 키: itemGrade',
  manufacturable_type INT COMMENT '원본 JSON 키: manufacturableType',
  attack_power INT COMMENT '원본 JSON 키: attackPower',
  defense INT COMMENT '원본 JSON 키: defense',
  skill_amp INT COMMENT '원본 JSON 키: skillAmp',
  max_hp INT COMMENT '원본 JSON 키: maxHp',
  hp_regen INT COMMENT '원본 JSON 키: hpRegen',
  attack_speed_ratio INT COMMENT '원본 JSON 키: attackSpeedRatio',
  critical_strike_chance INT COMMENT '원본 JSON 키: criticalStrikeChance',
  critical_strike_damage INT COMMENT '원본 JSON 키: criticalStrikeDamage',
  cooldown_reduction INT COMMENT '원본 JSON 키: cooldownReduction',
  life_steal INT COMMENT '원본 JSON 키: lifeSteal',
  move_speed FLOAT COMMENT '원본 JSON 키: moveSpeed',
  move_speed_ratio FLOAT COMMENT '원본 JSON 키: moveSpeedRatio',
  UNIQUE KEY uq_item_armor_version (item_id, season, major_version, minor_version)
) COMMENT '방어구 아이템 정보';

CREATE TABLE item_weapon (
  item_id INT COMMENT '원본 JSON 키: code',
  season INT,
  major_version INT,
  minor_version INT,
  item_name VARCHAR(255) COMMENT '원본 JSON 키: name',
  weapon_type VARCHAR(255) COMMENT '원본 JSON 키: weaponType',
  item_grade VARCHAR(255) COMMENT '원본 JSON 키: itemGrade',
  manufacturable_type INT COMMENT '원본 JSON 키: manufacturableType',
  attack_power INT COMMENT '원본 JSON 키: attackPower',
  defense INT COMMENT '원본 JSON 키: defense',
  skill_amp INT COMMENT '원본 JSON 키: skillAmp',
  max_hp INT COMMENT '원본 JSON 키: maxHp',
  attack_speed_ratio INT COMMENT '원본 JSON 키: attackSpeedRatio',
  critical_strike_chance INT COMMENT '원본 JSON 키: criticalStrikeChance',
  critical_strike_damage INT COMMENT '원본 JSON 키: criticalStrikeDamage',
  cooldown_reduction INT COMMENT '원본 JSON 키: cooldownReduction',
  life_steal INT COMMENT '원본 JSON 키: lifeSteal',
  attack_range FLOAT COMMENT '원본 JSON 키: attackRange',
  UNIQUE KEY uq_item_weapon_version (item_id, season, major_version, minor_version)
) COMMENT '무기 아이템 정보';

CREATE TABLE monster_info (
  monster_id INT COMMENT '원본 JSON 키: code',
  season INT,
  major_version INT,
  minor_version INT,
  monster_name VARCHAR(255) COMMENT '원본 JSON 키: monster',
  monster_grade VARCHAR(255) COMMENT '원본 JSON 키: grade',
  is_mutant BOOLEAN COMMENT '원본 JSON 키: isMutant',
  max_hp INT COMMENT '원본 JSON 키: maxHp',
  attack_power INT COMMENT '원본 JSON 키: attackPower',
  defense INT COMMENT '원본 JSON 키: defense',
  attack_speed FLOAT COMMENT '원본 JSON 키: attackSpeed',
  move_speed FLOAT COMMENT '원본 JSON 키: moveSpeed',
  attack_range FLOAT COMMENT '원본 JSON 키: attackRange',
  sight_range INT COMMENT '원본 JSON 키: sightRange',
  gain_exp INT COMMENT '원본 JSON 키: gainExp',
  UNIQUE KEY uq_monster_version (monster_id, season, major_version, minor_version)
) COMMENT '몬스터 정보';

CREATE TABLE trait_info (
  trait_id INT COMMENT 'l10n 파싱 데이터',
  season INT,
  major_version INT,
  minor_version INT,
  trait_name VARCHAR(255) COMMENT 'l10n 파싱 데이터',
  UNIQUE KEY uq_trait_version (trait_id, season, major_version, minor_version)
) COMMENT '특성 정보';

CREATE TABLE weather_info (
  weather_id INT COMMENT 'l10n 파싱 데이터',
  season INT,
  major_version INT,
  minor_version INT,
  weather_name VARCHAR(255) COMMENT 'l10n 파싱 데이터',
  UNIQUE KEY uq_weather_version (weather_id, season, major_version, minor_version)
) COMMENT '날씨 정보';


-- =================================================================================
-- 2. 수동 관리 정보 테이블
-- =================================================================================

CREATE TABLE armor_types (
  armor_id INT PRIMARY KEY,
  armor_name VARCHAR(255) UNIQUE
) COMMENT '방어구 타입 정보 (수동)';

CREATE TABLE weapon_types (
  weapon_id INT PRIMARY KEY,
  weapon_name VARCHAR(255) UNIQUE
) COMMENT '무기 타입 정보 (수동)';

CREATE TABLE tactical_skills (
  tactical_skill_id INT PRIMARY KEY,
  tactical_skill_name VARCHAR(255) UNIQUE
) COMMENT '전술 스킬 정보 (수동)';


-- =================================================================================
-- 3. 매치 데이터 테이블
-- =================================================================================

CREATE TABLE match_info (
  match_id BIGINT PRIMARY KEY COMMENT '원본 JSON 키: gameId',
  season_id INT COMMENT '원본 JSON 키: seasonId',
  version_season INT COMMENT '원본 JSON 키: versionSeason',
  version_major INT COMMENT '원본 JSON 키: versionMajor',
  version_minor INT COMMENT '원본 JSON 키: versionMinor',
  matching_mode INT COMMENT '원본 JSON 키: matchingMode',
  matching_team_mode INT COMMENT '원본 JSON 키: matchingTeamMode',
  server_name VARCHAR(255) COMMENT '원본 JSON 키: serverName',
  match_size INT COMMENT 'len(data["userGames"])',
  start_dtm DATETIME COMMENT '원본 JSON 키: startDtm',
  duration INT COMMENT '원본 JSON 키: totalTime (최소값)',
  expired_tm DATETIME,
  mmr_avg INT COMMENT '원본 JSON 키: mmrAvg',
  main_weather INT COMMENT '원본 JSON 키: mainWeather',
  sub_weather INT COMMENT '원본 JSON 키: subWeather',
  bot_added INT COMMENT '원본 JSON 키: botAdded',
  bot_remain INT COMMENT '원본 JSON 키: botRemain',
  safe_areas INT COMMENT '원본 JSON 키: safeAreas',
  restricted_area_accelerated INT COMMENT '원본 JSON 키: restrictedAreaAccelerated',
  INDEX idx_start_dtm (start_dtm),
  INDEX idx_matching_mode (matching_mode)
) COMMENT '매치 기본 정보';

CREATE TABLE match_team_info (
  match_id BIGINT NOT NULL,
  team_number INT NOT NULL COMMENT '원본 JSON 키: teamNumber',
  game_rank INT COMMENT '원본 JSON 키: gameRank',
  team_kill INT COMMENT '원본 JSON 키: teamKill',
  total_field_kill INT COMMENT '원본 JSON 키: totalFieldKill',
  team_elimination INT COMMENT '원본 JSON 키: teamElimination',
  team_down INT COMMENT '원본 JSON 키: teamDown',
  team_repeat_down INT COMMENT '원본 JSON 키: teamRepeatDown',
  team_battle_zone_down INT COMMENT '원본 JSON 키: teamBattleZoneDown',
  escape_state INT COMMENT '원본 JSON 키: escapeState',
  team_down_cannot_eliminate INT COMMENT '원본 JSON 키: teamDownCanNotEliminate 등',
  team_down_can_eliminate INT COMMENT '원본 JSON 키: teamDownCanEliminate 등',
  team_repeat_down_cannot_eliminate INT COMMENT '원본 JSON 키: teamRepeatDownCanNotEliminate 등',
  team_repeat_down_can_eliminate INT COMMENT '원본 JSON 키: teamRepeatDownCanEliminate 등',
  PRIMARY KEY (match_id, team_number),
  FOREIGN KEY (match_id) REFERENCES match_info (match_id) ON DELETE CASCADE
) COMMENT '매치 팀 정보';

CREATE TABLE match_user_start (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL COMMENT '원본 JSON 키: uid',
  nickname VARCHAR(128) NOT NULL NOT NULL COMMENT '원본 JSON 키: nickname',
  character_num INT COMMENT '원본 JSON 키: characterNum',
  language VARCHAR(255) COMMENT '원본 JSON 키: language',
  team_number INT COMMENT '원본 JSON 키: teamNumber',
  skin_code INT COMMENT '원본 JSON 키: skinCode',
  premade INT COMMENT '원본 JSON 키: preMade',
  except_premade_team INT COMMENT '원본 JSON 키: exceptPreMadeTeam',
  route_id_of_start INT COMMENT '원본 JSON 키: routeIdOfStart',
  place_of_start INT COMMENT '원본 JSON 키: placeOfStart',
  using_default_game_option BOOLEAN COMMENT '원본 JSON 키: usingDefaultGameOption',
  premade_matching_type INT COMMENT '원본 JSON 키: premadeMatchingType',
  tactical_skill_id INT COMMENT '원본 JSON 키: tacticalSkillGroup',
  ml_bot BOOLEAN COMMENT '원본 JSON 키: mlbot',
  PRIMARY KEY (match_id, uid),
  FOREIGN KEY (match_id, team_number) REFERENCES match_team_info (match_id, team_number) ON DELETE CASCADE,
  INDEX idx_uid (uid),
  INDEX idx_character_num (character_num),
  INDEX idx_tactical_skill_id (tactical_skill_id)
) COMMENT '매치 유저 정보 (중심 테이블)';

CREATE TABLE match_user_end (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  victory BOOLEAN COMMENT '원본 JSON 키: victory',
  play_time INT COMMENT '원본 JSON 키: playTime',
  watch_time INT COMMENT '원본 JSON 키: watchTime',
  total_time INT COMMENT '원본 JSON 키: totalTime',
  time_spent_in_briefing_room INT COMMENT '원본 JSON 키: timeSpentInBriefingRoom',
  craft_uncommon INT COMMENT '원본 JSON 키: craftUncommon',
  craft_rare INT COMMENT '원본 JSON 키: craftRare',
  craft_epic INT COMMENT '원본 JSON 키: craftEpic',
  craft_legend INT COMMENT '원본 JSON 키: craftLegend',
  craft_mythic INT COMMENT '원본 JSON 키: craftMythic',
  use_hyperloop INT COMMENT '원본 JSON 키: useHyperLoop',
  use_security_console INT COMMENT '원본 JSON 키: useSecurityConsole',
  break_count INT COMMENT '원본 JSON 키: breakCount',
  enter_dimension_rift INT COMMENT '원본 JSON 키: enterDimensionRift',
  enter_dimension_empowered_rift INT COMMENT '원본 JSON 키: enterDimensionEmpoweredRift',
  win_dimension_rift INT COMMENT '원본 JSON 키: winFromDimensionRift',
  win_dimension_empowered_rift INT COMMENT '원본 JSON 키: winFromDimensionEmpoweredRift',
  resurrectionkit_count INT COMMENT '원본 JSON 키: resurrectionKitUsageCount',
  resurrectionkit_credit_count INT COMMENT '원본 JSON 키: resurrectionKitCreditUsageCount',
  fishing_count INT COMMENT '원본 JSON 키: fishingCount',
  emoticon_count INT COMMENT '원본 JSON 키: useEmoticonCount',
  used_pairloop INT COMMENT '원본 JSON 키: usedPairLoop',
  give_up INT COMMENT '원본 JSON 키: giveUp',
  team_spectator INT COMMENT '원본 JSON 키: teamSpectator',
  is_leaving_before_credit_revival_terminate BOOLEAN COMMENT '원본 JSON 키: isLeavingBeforeCreditRevivalTerminate',
  PRIMARY KEY (match_id, uid),
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 기본 정보 (종료)';

CREATE TABLE match_user_combat (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  character_level INT COMMENT '원본 JSON 키: characterLevel',
  tactical_skill_level INT COMMENT '원본 JSON 키: tacticalSkillLevel',
  player_kill INT COMMENT '원본 JSON 키: playerKill',
  player_assistant INT COMMENT '원본 JSON 키: playerAssistant',
  player_deaths INT COMMENT '원본 JSON 키: playerDeaths',
  monster_kill INT COMMENT '원본 JSON 키: monsterKill',
  kills_phase_one INT COMMENT '원본 JSON 키: killsPhaseOne',
  kills_phase_two INT COMMENT '원본 JSON 키: killsPhaseTwo',
  kills_phase_three INT COMMENT '원본 JSON 키: killsPhaseThree',
  deaths_phase_one INT COMMENT '원본 JSON 키: deathsPhaseOne',
  deaths_phase_two INT COMMENT '원본 JSON 키: deathsPhaseTwo',
  deaths_phase_three INT COMMENT '원본 JSON 키: deathsPhaseThree',
  terminate_count INT COMMENT '원본 JSON 키: terminateCount',
  terminate_count_cannot_eliminate INT COMMENT '원본 JSON 키: terminateCountCanNotEliminate',
  clutch_count INT COMMENT '원본 JSON 키: clutchCount',
  unknown_kill INT COMMENT '원본 JSON 키: unknownKill',
  cc_time_to_player FLOAT COMMENT '원본 JSON 키: ccTimeToPlayer',
  credit_revival_count INT COMMENT '원본 JSON 키: creditRevivalCount',
  credit_revived_others_count INT COMMENT '원본 JSON 키: creditRevivedOthersCount',
  reunited_count INT COMMENT '원본 JSON 키: reunitedCount',
  tactical_skill_count INT COMMENT '원본 JSON 키: tacticalSkillUseCount',
  PRIMARY KEY (match_id, uid),
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 전투 정보';

CREATE TABLE match_user_trait (
    match_id BIGINT NOT NULL,
    uid VARCHAR(128) NOT NULL NOT NULL,
    trait_id INT NOT NULL COMMENT 'traitFirstSub, traitSecondSub 배열의 요소',
    trait_type VARCHAR(20) NOT NULL COMMENT '"first_sub" 또는 "second_sub"',
    FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE,
    UNIQUE KEY uq_user_trait (match_id, uid, trait_id)
) COMMENT '매치 유저 특성 정보 (정규화된 테이블)';

CREATE TABLE match_user_damage (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  damage_to_player_total INT COMMENT '원본 JSON 키: damageToPlayer',
  damage_to_player_basic INT COMMENT '원본 JSON 키: damageToPlayer_basic',
  damage_to_player_skill INT COMMENT '원본 JSON 키: damageToPlayer_skill',
  damage_to_player_item_skill INT COMMENT '원본 JSON 키: damageToPlayer_itemSkill',
  damage_to_player_direct INT COMMENT '원본 JSON 키: damageToPlayer_direct',
  damage_to_player_trap INT COMMENT '원본 JSON 키: damageToPlayer_trap',
  damage_to_player_unique_skill INT COMMENT '원본 JSON 키: damageToPlayer_uniqueSkill',
  damage_to_player_shield INT COMMENT '원본 JSON 키: damageToPlayer_Shield',
  damage_from_player_total INT COMMENT '원본 JSON 키: damageFromPlayer',
  damage_from_player_basic INT COMMENT '원본 JSON 키: damageFromPlayer_basic',
  damage_from_player_skill INT COMMENT '원본 JSON 키: damageFromPlayer_skill',
  damage_from_player_item_skill INT COMMENT '원본 JSON 키: damageFromPlayer_itemSkill',
  damage_from_player_direct INT COMMENT '원본 JSON 키: damageFromPlayer_direct',
  damage_from_player_trap INT COMMENT '원본 JSON 키: damageFromPlayer_trap',
  damage_from_player_unique_skill INT COMMENT '원본 JSON 키: damageFromPlayer_uniqueSkill',
  damage_to_monster_total INT COMMENT '원본 JSON 키: damageToMonster',
  damage_to_monster_basic INT COMMENT '원본 JSON 키: damageToMonster_basic',
  damage_to_monster_skill INT COMMENT '원본 JSON 키: damageToMonster_skill',
  damage_to_monster_item_skill INT COMMENT '원본 JSON 키: damageToMonster_itemSkill',
  damage_to_monster_direct INT COMMENT '원본 JSON 키: damageToMonster_direct',
  damage_to_monster_trap INT COMMENT '원본 JSON 키: damageToMonster_trap',
  damage_to_monster_unique_skill INT COMMENT '원본 JSON 키: damageToMonster_uniqueSkill',
  damage_from_monster_total INT COMMENT '원본 JSON 키: damageFromMonster',
  damage_offseted_by_shield_player INT COMMENT '원본 JSON 키: damageOffsetedByShield_Player',
  damage_offseted_by_shield_monster INT COMMENT '원본 JSON 키: damageOffsetedByShield_Monster',
  damage_to_guide_robot INT COMMENT '원본 JSON 키: damageToGuideRobot',
  heal_amount INT COMMENT '원본 JSON 키: healAmount',
  team_recover INT COMMENT '원본 JSON 키: teamRecover',
  protect_absorb INT COMMENT '원본 JSON 키: protectAbsorb',
  PRIMARY KEY (match_id, uid),
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 데미지 정보';

CREATE TABLE match_user_equipment (
    match_id BIGINT NOT NULL,
    uid VARCHAR(128) NOT NULL NOT NULL,
    first_weapon INT COMMENT '원본 JSON 키: equipFirstItemForLog["0"]',
    first_chest INT COMMENT '원본 JSON 키: equipFirstItemForLog["1"]',
    first_head INT COMMENT '원본 JSON 키: equipFirstItemForLog["2"]',
    first_arm INT COMMENT '원본 JSON 키: equipFirstItemForLog["3"]',
    first_leg INT COMMENT '원본 JSON 키: equipFirstItemForLog["4"]',
    last_weapon INT COMMENT '원본 JSON 키: equipment["0"]',
    last_chest INT COMMENT '원본 JSON 키: equipment["1"]',
    last_head INT COMMENT '원본 JSON 키: equipment["2"]',
    last_arm INT COMMENT '원본 JSON 키: equipment["3"]',
    last_leg INT COMMENT '원본 JSON 키: equipment["4"]',
    best_weapon INT COMMENT '원본 JSON 키: bestWeapon',
    best_weapon_level INT COMMENT '원본 JSON 키: bestWeaponLevel',
    PRIMARY KEY (match_id, uid),
    FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 장비 정보';

CREATE TABLE match_user_stats (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  max_hp INT COMMENT '원본 JSON 키: maxHp',
  hp_regen FLOAT COMMENT '원본 JSON 키: hpRegen',
  attack_power INT COMMENT '원본 JSON 키: attackPower',
  attack_speed FLOAT COMMENT '원본 JSON 키: attackSpeed',
  defense INT COMMENT '원본 JSON 키: defense',
  skill_amp INT COMMENT '원본 JSON 키: skillAmp',
  move_speed FLOAT COMMENT '원본 JSON 키: moveSpeed',
  ooc_move_speed FLOAT COMMENT '원본 JSON 키: outOfCombatMoveSpeed',
  sight_range INT COMMENT '원본 JSON 키: sightRange',
  attack_range FLOAT COMMENT '원본 JSON 키: attackRange',
  adaptive_force FLOAT COMMENT '원본 JSON 키: adaptiveForce',
  adaptive_force_attack FLOAT COMMENT '원본 JSON 키: adaptiveForceAttack',
  adaptive_force_amp FLOAT COMMENT '원본 JSON 키: adaptiveForceAmplify',
  critical_strike_chance FLOAT COMMENT '원본 JSON 키: criticalStrikeChance',
  critical_damage INT COMMENT '원본 JSON 키: criticalStrikeDamage',
  cooldown_reduction INT COMMENT '원본 JSON 키: coolDownReduction',
  life_steal INT COMMENT '원본 JSON 키: lifeSteal',
  normal_life_steal INT COMMENT '원본 JSON 키: normalLifeSteal',
  skill_life_steal INT COMMENT '원본 JSON 키: skillLifeSteal',
  PRIMARY KEY (match_id, uid),
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 스탯 정보';

CREATE TABLE match_user_mmr (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  mmr_before INT COMMENT '원본 JSON 키: mmrBefore',
  mmr_after INT COMMENT '원본 JSON 키: mmrAfter',
  mmr_gain INT COMMENT '원본 JSON 키: mmrGain',
  mmr_gain_in_game INT COMMENT '원본 JSON 키: mmrGainInGame',
  mmr_loss_entry_cost INT COMMENT '원본 JSON 키: mmrLossEntryCost',
  rank_point INT COMMENT '원본 JSON 키: rankPoint',
  PRIMARY KEY (match_id, uid),
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 MMR 정보';

CREATE TABLE match_user_sight (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  sight_score INT COMMENT '원본 JSON 키: viewContribution',
  camera_setup INT COMMENT '원본 JSON 키: addTelephotoCamera',
  camera_remove INT COMMENT '원본 JSON 키: removeTelephotoCamera',
  emp_drone_setup INT COMMENT '원본 JSON 키: useEmpDrone',
  basic_drone_setup INT COMMENT '원본 JSON 키: useReconDrone',
  PRIMARY KEY (match_id, uid),
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 시야 정보';

-- =================================================================================
-- 4. Long Format 데이터 테이블
-- =================================================================================

CREATE TABLE match_user_credit_acquisitions (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  acquisition_source VARCHAR(255) COMMENT '원본 JSON 키: creditSource의 key',
  acquisition_type VARCHAR(255) COMMENT '파싱 코드에서 매핑',
  credit_amount FLOAT COMMENT '원본 JSON 키: creditSource의 value',
  source_category VARCHAR(255) COMMENT '파싱 코드에서 매핑',
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE,
  INDEX idx_acquisition_source (acquisition_source)
) COMMENT '매치 유저 크레딧 획득 정보';

CREATE TABLE match_user_credit_expenditures (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  expenditure_item VARCHAR(255) COMMENT '파싱 코드에서 매핑',
  expenditure_type VARCHAR(255) COMMENT '파싱 코드에서 매핑',
  credit_amount INT,
  usage_count INT,
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE
) COMMENT '매치 유저 크레딧 소모 정보';

CREATE TABLE match_user_credit_time (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  minute INT COMMENT '0-19',
  used_credit INT COMMENT '원본 JSON 키: usedVFCredits[minute]',
  gain_credit INT COMMENT '원본 JSON 키: totalVFCredits[minute]',
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE,
  UNIQUE KEY uq_user_minute (match_id, uid, minute)
) COMMENT '매치 유저 분당 크레딧 정보';

CREATE TABLE match_user_object (
  match_id BIGINT NOT NULL,
  uid VARCHAR(128) NOT NULL NOT NULL,
  metric_type VARCHAR(255) COMMENT '파싱 코드에서 매핑',
  metric_name VARCHAR(255) COMMENT '파싱 코드에서 매핑',
  value INT,
  FOREIGN KEY (match_id, uid) REFERENCES match_user_start (match_id, uid) ON DELETE CASCADE,
  INDEX idx_metric_type_name (metric_type, metric_name)
) COMMENT '매치 유저 오브젝트/설치물 정보 (Long Format)';
