CREATE TABLE user (
    user_num INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Internal User ID',
    uid VARCHAR(128) NOT NULL UNIQUE COMMENT 'API User Identifier',
    nickname VARCHAR(30),
    last_match_id INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    last_updated_at DATETIME
);

CREATE INDEX ix_user_nickname ON user (nickname);

CREATE TABLE area_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    area_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    area_name VARCHAR(32),
    UNIQUE (
        area_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE character_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    character_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    character_name VARCHAR(32),
    archetype_primary VARCHAR(32),
    archetype_secondary VARCHAR(32),
    weapon_range_type VARCHAR(32),
    base_max_hp INT,
    base_attack_power INT,
    base_defense INT,
    base_skill_amp INT,
    base_hp_regen FLOAT,
    base_attack_speed FLOAT,
    base_move_speed FLOAT,
    base_sight_range FLOAT,
    UNIQUE (
        character_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE character_levelup_stats (
    character_info_id INT PRIMARY KEY,
    levelup_max_hp FLOAT,
    levelup_attack_power FLOAT,
    levelup_defense FLOAT,
    levelup_hp_regen FLOAT,
    FOREIGN KEY (character_info_id) REFERENCES character_info (id)
);

CREATE TABLE installation_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    installation_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    installation_name VARCHAR(32),
    UNIQUE (
        installation_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE item_armor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    item_name VARCHAR(32),
    item_type VARCHAR(16),
    armor_type VARCHAR(16),
    item_grade VARCHAR(16),
    manufacturable_type INT,
    attack_power INT,
    defense INT,
    skill_amp INT,
    max_hp INT,
    hp_regen INT,
    attack_speed_ratio INT,
    critical_strike_chance INT,
    critical_strike_damage INT,
    cooldown_reduction INT,
    life_steal INT,
    move_speed FLOAT,
    move_speed_ratio FLOAT,
    UNIQUE (
        item_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE item_weapon (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    item_name VARCHAR(32),
    weapon_type VARCHAR(16),
    item_grade VARCHAR(16),
    manufacturable_type INT,
    attack_power INT,
    defense INT,
    skill_amp INT,
    max_hp INT,
    attack_speed_ratio INT,
    critical_strike_chance INT,
    critical_strike_damage INT,
    cooldown_reduction INT,
    life_steal INT,
    attack_range FLOAT,
    UNIQUE (
        item_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE monster_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    monster_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    monster_name VARCHAR(32),
    monster_grade VARCHAR(16),
    is_mutant BOOLEAN,
    max_hp INT,
    attack_power INT,
    defense INT,
    attack_speed FLOAT,
    move_speed FLOAT,
    attack_range FLOAT,
    sight_range FLOAT,
    gain_exp INT,
    UNIQUE (
        monster_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE trait_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trait_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    trait_name VARCHAR(32),
    UNIQUE (
        trait_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE weather_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weather_id INT,
    season INT,
    major_version INT,
    minor_version INT,
    weather_name VARCHAR(16),
    UNIQUE (
        weather_id,
        season,
        major_version,
        minor_version
    )
);

CREATE TABLE armor_types (
    armor_id INT PRIMARY KEY,
    armor_name VARCHAR(32) UNIQUE
);

CREATE TABLE weapon_types (
    weapon_id INT PRIMARY KEY,
    weapon_name VARCHAR(32) UNIQUE
);

CREATE TABLE tactical_skills (
    tactical_skill_id INT PRIMARY KEY,
    tactical_skill_name VARCHAR(16) UNIQUE
);

CREATE TABLE match_info (
    match_id INT PRIMARY KEY,
    season_id INT,
    version_season INT,
    version_major INT,
    version_minor INT,
    matching_mode INT,
    matching_team_mode INT,
    server_name VARCHAR(32),
    match_size INT,
    start_dtm DATETIME,
    duration INT,
    expired_tm DATETIME,
    mmr_avg INT,
    main_weather_id INT,
    sub_weather_id INT,
    bot_added INT,
    bot_remain INT,
    safe_areas INT,
    restricted_area_accelerated INT,
    FOREIGN KEY (main_weather_id) REFERENCES weather_info (id),
    FOREIGN KEY (sub_weather_id) REFERENCES weather_info (id)
);

CREATE TABLE match_team_info (
    match_id INT,
    team_number INT,
    game_rank INT,
    team_kill INT,
    total_field_kill INT,
    team_elimination INT,
    team_down INT,
    team_repeat_down INT,
    team_battle_zone_down INT,
    escape_state INT,
    team_down_cannot_eliminate INT,
    team_down_can_eliminate INT,
    team_repeat_down_cannot_eliminate INT,
    team_repeat_down_can_eliminate INT,
    PRIMARY KEY (match_id, team_number),
    FOREIGN KEY (match_id) REFERENCES match_info (match_id)
);

CREATE TABLE match_user_start (
    match_id INT,
    user_num INT,
    nickname VARCHAR(32),
    character_info_id INT,
    language VARCHAR(32),
    team_number INT,
    skin_code INT,
    premade INT,
    except_premade_team INT,
    route_id_of_start INT,
    place_of_start INT,
    using_default_game_option BOOLEAN,
    premade_matching_type INT,
    tactical_skill_id INT,
    ml_bot BOOLEAN,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id) REFERENCES match_info (match_id),
    FOREIGN KEY (user_num) REFERENCES user (user_num),
    FOREIGN KEY (match_id, team_number) REFERENCES match_team_info (match_id, team_number),
    FOREIGN KEY (character_info_id) REFERENCES character_info (id),
    FOREIGN KEY (tactical_skill_id) REFERENCES tactical_skills (tactical_skill_id)
);

CREATE TABLE match_user_end (
    match_id INT,
    user_num INT,
    victory BOOLEAN,
    play_time INT,
    watch_time INT,
    total_time INT,
    time_spent_in_briefing_room INT,
    craft_uncommon INT,
    craft_rare INT,
    craft_epic INT,
    craft_legend INT,
    craft_mythic INT,
    use_hyperloop INT,
    use_security_console INT,
    break_count INT,
    enter_dimension_rift INT,
    enter_dimension_empowered_rift INT,
    win_dimension_rift INT,
    win_dimension_empowered_rift INT,
    resurrectionkit_count INT,
    resurrectionkit_credit_count INT,
    fishing_count INT,
    emoticon_count INT,
    used_pairloop INT,
    give_up INT,
    team_spectator INT,
    is_leaving_before_credit_revival_terminate BOOLEAN,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE match_user_combat (
    match_id INT,
    user_num INT,
    character_level INT,
    tactical_skill_level INT,
    player_kill INT,
    player_assistant INT,
    player_deaths INT,
    monster_kill INT,
    kills_phase_one INT,
    kills_phase_two INT,
    kills_phase_three INT,
    deaths_phase_one INT,
    deaths_phase_two INT,
    deaths_phase_three INT,
    terminate_count INT,
    terminate_count_cannot_eliminate INT,
    clutch_count INT,
    unknown_kill INT,
    cc_time_to_player FLOAT,
    credit_revival_count INT,
    credit_revived_others_count INT,
    reunited_count INT,
    tactical_skill_count INT,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE match_user_trait (
    match_id INT,
    user_num INT,
    trait_info_id INT,
    trait_type VARCHAR(16),
    PRIMARY KEY (
        match_id,
        user_num,
        trait_info_id,
        trait_type
    ),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num),
    FOREIGN KEY (trait_info_id) REFERENCES trait_info (id)
);

CREATE TABLE match_user_damage (
    match_id INT,
    user_num INT,
    damage_to_player_total INT,
    damage_to_player_basic INT,
    damage_to_player_skill INT,
    damage_to_player_item_skill INT,
    damage_to_player_direct INT,
    damage_to_player_trap INT,
    damage_to_player_unique_skill INT,
    damage_to_player_shield INT,
    damage_from_player_total INT,
    damage_from_player_basic INT,
    damage_from_player_skill INT,
    damage_from_player_item_skill INT,
    damage_from_player_direct INT,
    damage_from_player_trap INT,
    damage_from_player_unique_skill INT,
    damage_to_monster_total INT,
    damage_to_monster_basic INT,
    damage_to_monster_skill INT,
    damage_to_monster_item_skill INT,
    damage_to_monster_direct INT,
    damage_to_monster_trap INT,
    damage_to_monster_unique_skill INT,
    damage_from_monster_total INT,
    damage_offseted_by_shield_player INT,
    damage_offseted_by_shield_monster INT,
    damage_to_guide_robot INT,
    heal_amount INT,
    team_recover INT,
    protect_absorb INT,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE match_user_equipment (
    match_id INT,
    user_num INT,
    first_weapon_id INT,
    first_chest_id INT,
    first_head_id INT,
    first_arm_id INT,
    first_leg_id INT,
    last_weapon_id INT,
    last_chest_id INT,
    last_head_id INT,
    last_arm_id INT,
    last_leg_id INT,
    best_weapon_id INT,
    best_weapon_level INT,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num),
    FOREIGN KEY (first_weapon_id) REFERENCES item_weapon (id),
    FOREIGN KEY (last_weapon_id) REFERENCES item_weapon (id),
    FOREIGN KEY (best_weapon_id) REFERENCES item_weapon (id),
    FOREIGN KEY (first_chest_id) REFERENCES item_armor (id),
    FOREIGN KEY (first_head_id) REFERENCES item_armor (id),
    FOREIGN KEY (first_arm_id) REFERENCES item_armor (id),
    FOREIGN KEY (first_leg_id) REFERENCES item_armor (id),
    FOREIGN KEY (last_chest_id) REFERENCES item_armor (id),
    FOREIGN KEY (last_head_id) REFERENCES item_armor (id),
    FOREIGN KEY (last_arm_id) REFERENCES item_armor (id),
    FOREIGN KEY (last_leg_id) REFERENCES item_armor (id)
);

CREATE TABLE match_user_stats (
    match_id INT,
    user_num INT,
    max_hp INT,
    hp_regen FLOAT,
    attack_power INT,
    attack_speed FLOAT,
    defense INT,
    skill_amp INT,
    move_speed FLOAT,
    ooc_move_speed FLOAT,
    sight_range INT,
    attack_range FLOAT,
    adaptive_force FLOAT,
    adaptive_force_attack FLOAT,
    adaptive_force_amp FLOAT,
    critical_strike_chance FLOAT,
    critical_damage INT,
    cooldown_reduction INT,
    life_steal INT,
    normal_life_steal INT,
    skill_life_steal INT,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE match_user_mmr (
    match_id INT,
    user_num INT,
    mmr_before INT,
    mmr_after INT,
    mmr_gain INT,
    mmr_gain_in_game INT,
    mmr_loss_entry_cost INT,
    rank_point INT,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE match_user_sight (
    match_id INT,
    user_num INT,
    sight_score INT,
    camera_setup INT,
    camera_remove INT,
    emp_drone_setup INT,
    basic_drone_setup INT,
    PRIMARY KEY (match_id, user_num),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE credit_acquisition_source (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(64) UNIQUE
);

CREATE TABLE match_user_credit_acquisitions (
    match_id INT,
    user_num INT,
    acquisition_source_id INT,
    acquisition_type VARCHAR(32),
    credit_amount FLOAT,
    source_category VARCHAR(32),
    PRIMARY KEY (
        match_id,
        user_num,
        acquisition_source_id
    ),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num),
    FOREIGN KEY (acquisition_source_id) REFERENCES credit_acquisition_source (source_id)
);

CREATE TABLE credit_expenditure_source (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(64) UNIQUE
);

CREATE TABLE match_user_credit_expenditures (
    match_id INT,
    user_num INT,
    event_seq INT COMMENT 'Global purchase sequence for user',
    expenditure_source_id INT,
    expenditure_type VARCHAR(32),
    item_code INT COMMENT 'Raw item code if applicable',
    credit_amount INT,
    PRIMARY KEY (match_id, user_num, event_seq),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num),
    FOREIGN KEY (expenditure_source_id) REFERENCES credit_expenditure_source (source_id)
);

CREATE TABLE match_user_credit_time (
    match_id INT,
    user_num INT,
    minute INT,
    used_credit INT,
    gain_credit INT,
    PRIMARY KEY (match_id, user_num, minute),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE match_user_object (
    match_id INT,
    user_num INT,
    metric_type VARCHAR(32),
    metric_name VARCHAR(32),
    value INT,
    PRIMARY KEY (
        match_id,
        user_num,
        metric_type,
        metric_name
    ),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num)
);

CREATE TABLE match_user_gadget (
    match_id INT,
    user_num INT,
    gadget_info_id INT,
    gadget_count INT NOT NULL,
    PRIMARY KEY (
        match_id,
        user_num,
        gadget_info_id
    ),
    FOREIGN KEY (match_id, user_num) REFERENCES match_user_start (match_id, user_num),
    FOREIGN KEY (gadget_info_id) REFERENCES installation_info (id)
);