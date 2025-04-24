
CREATE TABLE equipment
(
  equipment_id    MEDIUMINT   NOT NULL,
  equipment_type  VARCHAR(16) NOT NULL,
  equipment_grade TINYINT     NOT NULL,
  equipment_name  VARCHAR(16) NOT NULL,
  PRIMARY KEY (equipment_id)
);

CREATE TABLE game_character
(
  character_id       INT         NOT NULL,
  character_name     VARCHAR(12) NOT NULL,
  attack_power       INT         NOT NULL,
  defense            INT         NOT NULL,
  skill_amp          INT         NOT NULL,
  max_hp             INT         NOT NULL,
  max_sp             INT         NOT NULL,
  hp_regen           INT         NOT NULL,
  sp_regen           INT         NOT NULL,
  attack_speed       INT         NOT NULL,
  attack_speed_limit INT         NOT NULL,
  move_speed         INT         NOT NULL,
  sight_range        INT         NOT NULL,
  PRIMARY KEY (character_id)
);

CREATE TABLE match_info
(
  match_id      INT       NOT NULL,
  start_dtm     TIMESTAMP NOT NULL,
  match_mode    TINYINT   NOT NULL COMMENT '솔로, 듀오, 스쿼드',
  season_id     SMALLINT  NOT NULL,
  version_major SMALLINT  NOT NULL,
  version_minor TINYINT   NOT NULL,
  weather_main  MEDIUMINT NOT NULL,
  weather_sub   MEDIUMINT NOT NULL,
  match_size    TINYINT   NOT NULL,
  match_avg_mmr SMALLINT  NOT NULL,
  match_expire_dtm    TIMESTAMP  NOT NULL,
  PRIMARY KEY (match_id)
);

CREATE TABLE match_team_info
(
  match_id                                 INT       NOT NULL,
  team_id                                  INT       NOT NULL,
  team_ranking                             TINYINT   NOT NULL,
  escape_state                             TINYINT   NOT NULL,
  player_down                              TINYINT   NOT NULL,
  team_down_in_auto_reserrection           TINYINT   NOT NULL,
  team_down_after_auto_reserrection        TINYINT   NOT NULL,
  team_repeat_down_in_auto_reserrection    TINYINT   NOT NULL,
  team_repeat_down_after_auto_reserrection TINYINT   NOT NULL,
  team_elimination_count                   TINYINT   NOT NULL,
  PRIMARY KEY (match_id, team_id)
);

CREATE TABLE match_user_basic
(
  match_id                    INT       NOT NULL,
  user_id                     INT       NOT NULL,
  team_id                     TINYINT   NOT NULL,
  except_premade_team         BOOL      NOT NULL DEFAULT false,
  character_id                INT       NOT NULL,
  skin_id                     INT       NOT NULL,
  character_level             TINYINT   NOT NULL,
  total_kill                  TINYINT   NOT NULL,
  total_death                 TINYINT   NOT NULL,
  total_assist                TINYINT   NOT NULL,
  weapon_type                 SMALLINT  NOT NULL,
  weapon_level                TINYINT   NOT NULL,
  play_time                   SMALLINT  NOT NULL,
  watch_time                  SMALLINT  NOT NULL,
  total_damage_to_player      MEDIUMINT NOT NULL,
  total_damage_from_player    MEDIUMINT NOT NULL,
  total_heal                  MEDIUMINT NOT NULL,
  heal_to_team                MEDIUMINT NOT NULL,
  use_loop_count              SMALLINT  NOT NULL,
  user_security_console_count SMALLINT  NOT NULL,
  route_id                    MEDIUMINT NOT NULL,
  start_place                 SMALLINT  NOT NULL,
  emotion_count               SMALLINT  NOT NULL,
  fishing_count               SMALLINT  NOT NULL,
  tactical_skill_id           SMALLINT  NOT NULL,
  tactical_skill_level        TINYINT   NOT NULL,
  tactical_skill_count        SMALLINT  NOT NULL,
  credit_revival_count        TINYINT   NOT NULL,
  credit_revival_other_count  TINYINT   NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_credit_time
(
  match_id    INT      NOT NULL,
  user_id     INT      NOT NULL,
  minute      TINYINT  NOT NULL,
  used_credit SMALLINT NOT NULL,
  gain_credit SMALLINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_damage
(
  match_id                  INT       NOT NULL,
  user_id                   INT       NOT NULL,
  basic_damage_to_player    MEDIUMINT NOT NULL,
  skill_damage_to_player    MEDIUMINT NOT NULL,
  direct_damage_to_player   MEDIUMINT NOT NULL,
  shield_damage_to_player   MEDIUMINT NOT NULL,
  item_damage_to_player     MEDIUMINT NOT NULL,
  trap_damage_to_player     MEDIUMINT NOT NULL,
  basic_damage_from_player  MEDIUMINT NOT NULL,
  skill_damage_from_player  MEDIUMINT NOT NULL,
  direct_damage_from_player MEDIUMINT NOT NULL,
  shield_damage_from_player MEDIUMINT NOT NULL,
  item_damage_from_player   MEDIUMINT NOT NULL,
  trap_damage_from_player   MEDIUMINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_equipment
(
  match_id               INT       NOT NULL,
  user_id                INT       NOT NULL,
  equipment_weapon       MEDIUMINT NOT NULL    ,
  equipment_chest        MEDIUMINT NOT NULL,
  equipment_head         MEDIUMINT NOT NULL,
  equipment_arm          MEDIUMINT NOT NULL,
  equipment_leg          MEDIUMINT NOT NULL,
  first_equipment_weapon MEDIUMINT NOT NULL,
  first_equipment_chest  MEDIUMINT NOT NULL,
  first_equipment_head   MEDIUMINT NOT NULL,
  first_equipment_arm    MEDIUMINT NOT NULL,
  first_equipment_leg    MEDIUMINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_gain_credit
(
  match_id             INT      NOT NULL,
  user_id              INT      NOT NULL,
  total_gain_cr        SMALLINT NOT NULL,
  start_cr             SMALLINT NOT NULL,
  time_elapse_cr       SMALLINT NOT NULL    ,
  time_elapse_bonus_cr SMALLINT NOT NULL,
  wild_dog_cr          SMALLINT NOT NULL,
  bat_cr               SMALLINT NOT NULL,
  chicken_cr           SMALLINT NOT NULL,
  boar_cr              SMALLINT NOT NULL,
  wolf_cr              SMALLINT NOT NULL,
  bear_cr              SMALLINT NOT NULL,
  raven_cr             SMALLINT NOT NULL,
  mutant_wild_dog_cr   SMALLINT NOT NULL,
  mutant_bat_cr        SMALLINT NOT NULL,
  mutant_chicken_cr    SMALLINT NOT NULL,
  mutant_boar_cr       SMALLINT NOT NULL,
  mutant_wolf_cr       SMALLINT NOT NULL,
  mutant_bear_cr       SMALLINT NOT NULL,
  mutant_raven_cr      SMALLINT NOT NULL,
  alpha_cr             SMALLINT NOT NULL,
  omega_cr             SMALLINT NOT NULL,
  gamma_cr             SMALLINT NOT NULL,
  wickline_cr          SMALLINT NOT NULL,
  security_console_cr  SMALLINT NOT NULL,
  drone_cr             SMALLINT NOT NULL,
  kill_cr              SMALLINT NOT NULL,
  kill_by_team_cr      SMALLINT NOT NULL,
  rumi_cr              SMALLINT NOT NULL,
  skill_cr             SMALLINT NULL    ,
  cointoss_cr          SMALLINT NULL    ,
  item_bounty_cr       SMALLINT NOT NULL,
  kill_bounty_cr       SMALLINT NOT NULL,
  door_console_cr      SMALLINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_mmr
(
  match_id       INT      NOT NULL,
  user_id        INT      NOT NULL,
  before_mmr     SMALLINT NOT NULL,
  after_mmr      SMALLINT NOT NULL,
  mmr_gain       SMALLINT NOT NULL,
  mmr_entry_loss SMALLINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_sight
(
  match_id          INT     NOT NULL,
  user_id           INT     NOT NULL,
  sight_score       TINYINT NOT NULL DEFAULT 0,
  camera_setup      TINYINT NOT NULL DEFAULT 0,
  camera_remove     TINYINT NOT NULL DEFAULT 0,
  emp_drone_setup   TINYINT NOT NULL DEFAULT 0,
  basic_drone_setup TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_stat
(
  match_id              INT      NOT NULL,
  user_id               INT      NOT NULL,
  hp                    SMALLINT NOT NULL,
  sp                    SMALLINT NOT NULL,
  hp_regen              SMALLINT NOT NULL,
  sp_regen              SMALLINT NOT NULL,
  depense               SMALLINT NOT NULL,
  attack_power          SMALLINT NOT NULL,
  attack_speed          SMALLINT NOT NULL,
  skill_amp             SMALLINT NOT NULL,
  cooldown_percent      FLOAT    NOT NULL,
  adaptive_force        SMALLINT NOT NULL,
  adaptive_force_attack SMALLINT NOT NULL,
  adaptive_force_amp    SMALLINT NOT NULL,
  move_speed            FLOAT    NOT NULL,
  ooc_move_speed        FLOAT    NOT NULL,
  sight_range           FLOAT    NOT NULL,
  attack_range          FLOAT    NOT NULL,
  critical_percent      TINYINT  NOT NULL,
  critical_damage       SMALLINT NOT NULL,
  life_steal_percent    FLOAT    NOT NULL,
  normal_life_steel     SMALLINT NOT NULL,
  skill_life_steel      SMALLINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE match_user_trait
(
  user_id          INT NOT NULL,
  match_id         INT NOT NULL,
  core_trait_id    INT NOT NULL,
  first_trait_id1  INT NOT NULL,
  first_trait_id2  INT NOT NULL,
  second_trait_id1 INT NOT NULL,
  second_trait_id2 INT NOT NULL,
  PRIMARY KEY (user_id, match_id)
);

CREATE TABLE match_user_use_credit
(
  match_id                    INT      NOT NULL,
  user_id                     INT      NOT NULL,
  total_used_cr               SMALLINT NOT NULL,
  used_revival_cr             SMALLINT NOT NULL,
  used_remote_drone_myself_cr SMALLINT NOT NULL,
  used_remote_drone_myteam_cr SMALLINT NOT NULL,
  used_tactical_skill_cr      SMALLINT NOT NULL,
  used_tree_of_life_cr        SMALLINT NOT NULL,
  used_meteorite_cr           SMALLINT NOT NULL,
  used_mythril_cr             SMALLINT NOT NULL,
  used_forcecore_cr           SMALLINT NOT NULL,
  used_blood_sample_cr        SMALLINT NOT NULL,
  used_escapekit_cr           SMALLINT NOT NULL,
  used_emp_drone_cr           SMALLINT NOT NULL,
  used_basic_drone_cr         SMALLINT NOT NULL,
  used_camera_cr              SMALLINT NOT NULL,
  used_guillotine_cr          SMALLINT NOT NULL,
  used_c4_cr                  SMALLINT NOT NULL,
  used_fried_chicken_cr       SMALLINT NOT NULL,
  used_rumi_signiture_cr      SMALLINT NOT NULL,
  used_rumi_fragship_cr       SMALLINT NOT NULL,
  used_rumi_radial_cr         SMALLINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE monster_info
(
  monster_id   INT         NOT NULL,
  monster_name VARCHAR(16) NOT NULL,
  PRIMARY KEY (monster_id)
);

CREATE TABLE object
(
  match_id              INT       NOT NULL,
  user_id               INT       NOT NULL,
  damage_to_rumi        MEDIUMINT NOT NULL,
  damage_to_monster     MEDIUMINT NOT NULL,
  total_kill_monster    SMALLINT  NOT NULL,
  kill_alpha            TINYINT   NOT NULL,
  kill_omega            TINYINT   NOT NULL,
  kill_gamma            TINYINT   NOT NULL,
  kill_wickline         BOOL      NOT NULL DEFAULT 0,
  get_cube_red          TINYINT   NOT NULL,
  get_cube_green        TINYINT   NOT NULL,
  get_cube_gold         TINYINT   NOT NULL,
  get_cube_purple       TINYINT   NOT NULL,
  get_cube_skyblue      TINYINT   NOT NULL,
  collect_tree_of_life  TINYINT   NOT NULL,
  collect_meteorite     TINYINT   NOT NULL,
  get_air_supply_purple TINYINT   NOT NULL,
  get_air_supply_red    TINYINT   NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

CREATE TABLE trait_info
(
  trait_id   INT      NOT NULL,
  trait_name CHAR(50) NOT NULL,
  PRIMARY KEY (trait_id)
);

CREATE TABLE user
(
  user_id       INT         NOT NULL,
  nickname      VARCHAR(16) NOT NULL,
  user_language VARCHAR(16) NOT NULL,
  PRIMARY KEY (user_id)
);

CREATE TABLE user_match_kda_detail
(
  match_id          INT     NOT NULL,
  user_id           INT     NOT NULL,
  kill_phase_one    TINYINT NOT NULL,
  kill_phase_two    TINYINT NOT NULL,
  kill_phase_three  TINYINT NOT NULL,
  death_phase_one   TINYINT NOT NULL,
  death_phase_two   TINYINT NOT NULL,
  death_phase_three TINYINT NOT NULL,
  PRIMARY KEY (match_id, user_id)
);

ALTER TABLE match_user_basic
  ADD CONSTRAINT FK_user_TO_match_user_basic
    FOREIGN KEY (user_id)
    REFERENCES user (user_id);

ALTER TABLE match_user_basic
  ADD CONSTRAINT FK_match_info_TO_match_user_basic
    FOREIGN KEY (match_id)
    REFERENCES match_info (match_id);

ALTER TABLE match_user_basic
  ADD CONSTRAINT FK_game_character_TO_match_user_basic
    FOREIGN KEY (character_id)
    REFERENCES game_character (character_id);

ALTER TABLE match_team_info
  ADD CONSTRAINT FK_match_info_TO_match_team_info
    FOREIGN KEY (match_id)
    REFERENCES match_info (match_id);

ALTER TABLE match_user_credit_time
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_credit_time
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_damage
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_damage
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_equipment
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_equipment
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_gain_credit
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_gain_credit
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_mmr
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_mmr
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_sight
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_sight
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_stat
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_stat
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_trait
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_trait
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE match_user_use_credit
  ADD CONSTRAINT FK_match_user_basic_TO_match_user_use_credit
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE object
  ADD CONSTRAINT FK_match_user_basic_TO_object
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

ALTER TABLE user_match_kda_detail
  ADD CONSTRAINT FK_match_user_basic_TO_user_match_kda_detail
    FOREIGN KEY (match_id, user_id)
    REFERENCES match_user_basic (match_id, user_id);

-- match_user_equipment, equipment
ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_equipment_weapon
    FOREIGN KEY (equipment_weapon) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_equipment_chest
    FOREIGN KEY (equipment_chest) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_equipment_head
    FOREIGN KEY (equipment_head) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_equipment_arm
    FOREIGN KEY (equipment_arm) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_equipment_leg
    FOREIGN KEY (equipment_leg) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_first_equipment_weapon
    FOREIGN KEY (first_equipment_weapon) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_first_equipment_chest
    FOREIGN KEY (first_equipment_chest) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_first_equipment_head
    FOREIGN KEY (first_equipment_head) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_first_equipment_arm
    FOREIGN KEY (first_equipment_arm) REFERENCES equipment(equipment_id);

ALTER TABLE match_user_equipment
ADD CONSTRAINT fk_first_equipment_leg
    FOREIGN KEY (first_equipment_leg) REFERENCES equipment(equipment_id);

-- trait
ALTER TABLE match_user_trait
ADD CONSTRAINT fk_core_trait_id
    FOREIGN KEY (core_trait_id) REFERENCES trait_info(trait_id);

ALTER TABLE match_user_trait
ADD CONSTRAINT fk_first_trait_id1
    FOREIGN KEY (first_trait_id1) REFERENCES trait_info(trait_id);

ALTER TABLE match_user_trait
ADD CONSTRAINT fk_first_trait_id2
    FOREIGN KEY (first_trait_id2) REFERENCES trait_info(trait_id);

ALTER TABLE match_user_trait
ADD CONSTRAINT fk_second_trait_id1
    FOREIGN KEY (second_trait_id1) REFERENCES trait_info(trait_id);

ALTER TABLE match_user_trait
ADD CONSTRAINT fk_second_trait_id2
    FOREIGN KEY (second_trait_id2) REFERENCES trait_info(trait_id);