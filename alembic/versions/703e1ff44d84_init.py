"""init

Revision ID: 703e1ff44d84
Revises: 
Create Date: 2026-01-03 22:42:18.837197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '703e1ff44d84'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Basic Info Tables ---
    op.create_table('user',
        sa.Column('user_num', sa.Integer(), autoincrement=True, nullable=False, comment='Internal User ID'),
        sa.Column('uid', sa.String(length=128), nullable=False, comment='API User Identifier'),
        sa.Column('nickname', sa.String(length=30), nullable=True),
        sa.Column('last_match_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('user_num'),
        sa.UniqueConstraint('uid')
    )
    op.create_index(op.f('ix_user_nickname'), 'user', ['nickname'], unique=False)

    op.create_table('area_info',
        sa.Column('area_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('area_name', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('area_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('character_info',
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('character_name', sa.String(length=32), nullable=True),
        sa.Column('archetype_primary', sa.String(length=32), nullable=True),
        sa.Column('archetype_secondary', sa.String(length=32), nullable=True),
        sa.Column('weapon_range_type', sa.String(length=32), nullable=True),
        sa.Column('base_max_hp', sa.Integer(), nullable=True),
        sa.Column('base_attack_power', sa.Integer(), nullable=True),
        sa.Column('base_defense', sa.Integer(), nullable=True),
        sa.Column('base_skill_amp', sa.Integer(), nullable=True),
        sa.Column('base_hp_regen', sa.Float(), nullable=True),
        sa.Column('base_attack_speed', sa.Float(), nullable=True),
        sa.Column('base_move_speed', sa.Float(), nullable=True),
        sa.Column('base_sight_range', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('character_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('character_levelup_stats',
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('levelup_max_hp', sa.Float(), nullable=True),
        sa.Column('levelup_attack_power', sa.Float(), nullable=True),
        sa.Column('levelup_defense', sa.Float(), nullable=True),
        sa.Column('levelup_hp_regen', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('character_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('installation_info',
        sa.Column('installation_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('installation_name', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('installation_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('item_armor',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('item_name', sa.String(length=32), nullable=True),
        sa.Column('item_type', sa.String(length=16), nullable=True),
        sa.Column('armor_type', sa.String(length=16), nullable=True),
        sa.Column('item_grade', sa.String(length=16), nullable=True),
        sa.Column('manufacturable_type', sa.Integer(), nullable=True),
        sa.Column('attack_power', sa.Integer(), nullable=True),
        sa.Column('defense', sa.Integer(), nullable=True),
        sa.Column('skill_amp', sa.Integer(), nullable=True),
        sa.Column('max_hp', sa.Integer(), nullable=True),
        sa.Column('hp_regen', sa.Integer(), nullable=True),
        sa.Column('attack_speed_ratio', sa.Integer(), nullable=True),
        sa.Column('critical_strike_chance', sa.Integer(), nullable=True),
        sa.Column('critical_strike_damage', sa.Integer(), nullable=True),
        sa.Column('cooldown_reduction', sa.Integer(), nullable=True),
        sa.Column('life_steal', sa.Integer(), nullable=True),
        sa.Column('move_speed', sa.Float(), nullable=True),
        sa.Column('move_speed_ratio', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('item_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('item_weapon',
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('item_name', sa.String(length=32), nullable=True),
        sa.Column('weapon_type', sa.String(length=16), nullable=True),
        sa.Column('item_grade', sa.String(length=16), nullable=True),
        sa.Column('manufacturable_type', sa.Integer(), nullable=True),
        sa.Column('attack_power', sa.Integer(), nullable=True),
        sa.Column('defense', sa.Integer(), nullable=True),
        sa.Column('skill_amp', sa.Integer(), nullable=True),
        sa.Column('max_hp', sa.Integer(), nullable=True),
        sa.Column('attack_speed_ratio', sa.Integer(), nullable=True),
        sa.Column('critical_strike_chance', sa.Integer(), nullable=True),
        sa.Column('critical_strike_damage', sa.Integer(), nullable=True),
        sa.Column('cooldown_reduction', sa.Integer(), nullable=True),
        sa.Column('life_steal', sa.Integer(), nullable=True),
        sa.Column('attack_range', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('item_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('monster_info',
        sa.Column('monster_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('monster_name', sa.String(length=32), nullable=True),
        sa.Column('monster_grade', sa.String(length=16), nullable=True),
        sa.Column('is_mutant', sa.Boolean(), nullable=True),
        sa.Column('max_hp', sa.Integer(), nullable=True),
        sa.Column('attack_power', sa.Integer(), nullable=True),
        sa.Column('defense', sa.Integer(), nullable=True),
        sa.Column('attack_speed', sa.Float(), nullable=True),
        sa.Column('move_speed', sa.Float(), nullable=True),
        sa.Column('attack_range', sa.Float(), nullable=True),
        sa.Column('sight_range', sa.Integer(), nullable=True),
        sa.Column('gain_exp', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('monster_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('trait_info',
        sa.Column('trait_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('trait_name', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('trait_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('weather_info',
        sa.Column('weather_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('major_version', sa.Integer(), nullable=False),
        sa.Column('minor_version', sa.Integer(), nullable=False),
        sa.Column('weather_name', sa.String(length=16), nullable=True),
        sa.PrimaryKeyConstraint('weather_id', 'season', 'major_version', 'minor_version')
    )

    op.create_table('armor_types',
        sa.Column('armor_id', sa.Integer(), nullable=False),
        sa.Column('armor_name', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('armor_id'),
        sa.UniqueConstraint('armor_name')
    )

    op.create_table('weapon_types',
        sa.Column('weapon_id', sa.Integer(), nullable=False),
        sa.Column('weapon_name', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('weapon_id'),
        sa.UniqueConstraint('weapon_name')
    )

    op.create_table('tactical_skills',
        sa.Column('tactical_skill_id', sa.Integer(), nullable=False),
        sa.Column('tactical_skill_name', sa.String(length=16), nullable=True),
        sa.PrimaryKeyConstraint('tactical_skill_id'),
        sa.UniqueConstraint('tactical_skill_name')
    )
    
    op.create_table('credit_acquisition_source',
        sa.Column('source_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_name', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('source_id'),
        sa.UniqueConstraint('source_name')
    )
    
    op.create_table('credit_expenditure_source',
        sa.Column('source_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_name', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('source_id'),
        sa.UniqueConstraint('source_name')
    )

    # --- Match Info Tables ---
    op.create_table('match_info',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('season_id', sa.Integer(), nullable=True),
        sa.Column('version_season', sa.Integer(), nullable=True),
        sa.Column('version_major', sa.Integer(), nullable=True),
        sa.Column('version_minor', sa.Integer(), nullable=True),
        sa.Column('matching_mode', sa.Integer(), nullable=True),
        sa.Column('matching_team_mode', sa.Integer(), nullable=True),
        sa.Column('server_name', sa.String(length=32), nullable=True),
        sa.Column('match_size', sa.Integer(), nullable=True),
        sa.Column('start_dtm', sa.DateTime(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('expired_tm', sa.DateTime(), nullable=True),
        sa.Column('mmr_avg', sa.Integer(), nullable=True),
        sa.Column('main_weather', sa.Integer(), nullable=True),
        sa.Column('sub_weather', sa.Integer(), nullable=True),
        sa.Column('bot_added', sa.Integer(), nullable=True),
        sa.Column('bot_remain', sa.Integer(), nullable=True),
        sa.Column('safe_areas', sa.Integer(), nullable=True),
        sa.Column('restricted_area_accelerated', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('match_id')
    )

    op.create_table('match_team_info',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('team_number', sa.Integer(), nullable=False),
        sa.Column('game_rank', sa.Integer(), nullable=True),
        sa.Column('team_kill', sa.Integer(), nullable=True),
        sa.Column('total_field_kill', sa.Integer(), nullable=True),
        sa.Column('team_elimination', sa.Integer(), nullable=True),
        sa.Column('team_down', sa.Integer(), nullable=True),
        sa.Column('team_repeat_down', sa.Integer(), nullable=True),
        sa.Column('team_battle_zone_down', sa.Integer(), nullable=True),
        sa.Column('escape_state', sa.Integer(), nullable=True),
        sa.Column('team_down_cannot_eliminate', sa.Integer(), nullable=True),
        sa.Column('team_down_can_eliminate', sa.Integer(), nullable=True),
        sa.Column('team_repeat_down_cannot_eliminate', sa.Integer(), nullable=True),
        sa.Column('team_repeat_down_can_eliminate', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_info.match_id'], ),
        sa.PrimaryKeyConstraint('match_id', 'team_number')
    )

    op.create_table('match_user_start',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('nickname', sa.String(length=32), nullable=True),
        sa.Column('character_num', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=32), nullable=True),
        sa.Column('team_number', sa.Integer(), nullable=True),
        sa.Column('skin_code', sa.Integer(), nullable=True),
        sa.Column('premade', sa.Integer(), nullable=True),
        sa.Column('except_premade_team', sa.Integer(), nullable=True),
        sa.Column('route_id_of_start', sa.Integer(), nullable=True),
        sa.Column('place_of_start', sa.Integer(), nullable=True),
        sa.Column('using_default_game_option', sa.Boolean(), nullable=True),
        sa.Column('premade_matching_type', sa.Integer(), nullable=True),
        sa.Column('tactical_skill_id', sa.Integer(), nullable=True),
        sa.Column('ml_bot', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_team_info.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['user.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )

    op.create_table('match_user_end',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('victory', sa.Boolean(), nullable=True),
        sa.Column('play_time', sa.Integer(), nullable=True),
        sa.Column('watch_time', sa.Integer(), nullable=True),
        sa.Column('total_time', sa.Integer(), nullable=True),
        sa.Column('time_spent_in_briefing_room', sa.Integer(), nullable=True),
        sa.Column('craft_uncommon', sa.Integer(), nullable=True),
        sa.Column('craft_rare', sa.Integer(), nullable=True),
        sa.Column('craft_epic', sa.Integer(), nullable=True),
        sa.Column('craft_legend', sa.Integer(), nullable=True),
        sa.Column('craft_mythic', sa.Integer(), nullable=True),
        sa.Column('use_hyperloop', sa.Integer(), nullable=True),
        sa.Column('use_security_console', sa.Integer(), nullable=True),
        sa.Column('break_count', sa.Integer(), nullable=True),
        sa.Column('enter_dimension_rift', sa.Integer(), nullable=True),
        sa.Column('enter_dimension_empowered_rift', sa.Integer(), nullable=True),
        sa.Column('win_dimension_rift', sa.Integer(), nullable=True),
        sa.Column('win_dimension_empowered_rift', sa.Integer(), nullable=True),
        sa.Column('resurrectionkit_count', sa.Integer(), nullable=True),
        sa.Column('resurrectionkit_credit_count', sa.Integer(), nullable=True),
        sa.Column('fishing_count', sa.Integer(), nullable=True),
        sa.Column('emoticon_count', sa.Integer(), nullable=True),
        sa.Column('used_pairloop', sa.Integer(), nullable=True),
        sa.Column('give_up', sa.Integer(), nullable=True),
        sa.Column('team_spectator', sa.Integer(), nullable=True),
        sa.Column('is_leaving_before_credit_revival_terminate', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )

    op.create_table('match_user_combat',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('character_level', sa.Integer(), nullable=True),
        sa.Column('tactical_skill_level', sa.Integer(), nullable=True),
        sa.Column('player_kill', sa.Integer(), nullable=True),
        sa.Column('player_assistant', sa.Integer(), nullable=True),
        sa.Column('player_deaths', sa.Integer(), nullable=True),
        sa.Column('monster_kill', sa.Integer(), nullable=True),
        sa.Column('kills_phase_one', sa.Integer(), nullable=True),
        sa.Column('kills_phase_two', sa.Integer(), nullable=True),
        sa.Column('kills_phase_three', sa.Integer(), nullable=True),
        sa.Column('deaths_phase_one', sa.Integer(), nullable=True),
        sa.Column('deaths_phase_two', sa.Integer(), nullable=True),
        sa.Column('deaths_phase_three', sa.Integer(), nullable=True),
        sa.Column('terminate_count', sa.Integer(), nullable=True),
        sa.Column('terminate_count_cannot_eliminate', sa.Integer(), nullable=True),
        sa.Column('clutch_count', sa.Integer(), nullable=True),
        sa.Column('unknown_kill', sa.Integer(), nullable=True),
        sa.Column('cc_time_to_player', sa.Float(), nullable=True),
        sa.Column('credit_revival_count', sa.Integer(), nullable=True),
        sa.Column('credit_revived_others_count', sa.Integer(), nullable=True),
        sa.Column('reunited_count', sa.Integer(), nullable=True),
        sa.Column('tactical_skill_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )
    
    op.create_table('match_user_trait',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('trait_id', sa.Integer(), nullable=False),
        sa.Column('trait_type', sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num', 'trait_id', 'trait_type')
    )

    op.create_table('match_user_damage',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('damage_to_player_total', sa.Integer(), nullable=True),
        sa.Column('damage_to_player_basic', sa.Integer(), nullable=True),
        sa.Column('damage_to_player_skill', sa.Integer(), nullable=True),
        sa.Column('damage_to_player_item_skill', sa.Integer(), nullable=True),
        sa.Column('damage_to_player_direct', sa.Integer(), nullable=True),
        sa.Column('damage_to_player_trap', sa.Integer(), nullable=True),
        sa.Column('damage_to_player_unique_skill', sa.Integer(), nullable=True),
        sa.Column('damage_to_player_shield', sa.Integer(), nullable=True),
        sa.Column('damage_from_player_total', sa.Integer(), nullable=True),
        sa.Column('damage_from_player_basic', sa.Integer(), nullable=True),
        sa.Column('damage_from_player_skill', sa.Integer(), nullable=True),
        sa.Column('damage_from_player_item_skill', sa.Integer(), nullable=True),
        sa.Column('damage_from_player_direct', sa.Integer(), nullable=True),
        sa.Column('damage_from_player_trap', sa.Integer(), nullable=True),
        sa.Column('damage_from_player_unique_skill', sa.Integer(), nullable=True),
        sa.Column('damage_to_monster_total', sa.Integer(), nullable=True),
        sa.Column('damage_to_monster_basic', sa.Integer(), nullable=True),
        sa.Column('damage_to_monster_skill', sa.Integer(), nullable=True),
        sa.Column('damage_to_monster_item_skill', sa.Integer(), nullable=True),
        sa.Column('damage_to_monster_direct', sa.Integer(), nullable=True),
        sa.Column('damage_to_monster_trap', sa.Integer(), nullable=True),
        sa.Column('damage_to_monster_unique_skill', sa.Integer(), nullable=True),
        sa.Column('damage_from_monster_total', sa.Integer(), nullable=True),
        sa.Column('damage_offseted_by_shield_player', sa.Integer(), nullable=True),
        sa.Column('damage_offseted_by_shield_monster', sa.Integer(), nullable=True),
        sa.Column('damage_to_guide_robot', sa.Integer(), nullable=True),
        sa.Column('heal_amount', sa.Integer(), nullable=True),
        sa.Column('team_recover', sa.Integer(), nullable=True),
        sa.Column('protect_absorb', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )

    op.create_table('match_user_equipment',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('first_weapon', sa.Integer(), nullable=True),
        sa.Column('first_chest', sa.Integer(), nullable=True),
        sa.Column('first_head', sa.Integer(), nullable=True),
        sa.Column('first_arm', sa.Integer(), nullable=True),
        sa.Column('first_leg', sa.Integer(), nullable=True),
        sa.Column('last_weapon', sa.Integer(), nullable=True),
        sa.Column('last_chest', sa.Integer(), nullable=True),
        sa.Column('last_head', sa.Integer(), nullable=True),
        sa.Column('last_arm', sa.Integer(), nullable=True),
        sa.Column('last_leg', sa.Integer(), nullable=True),
        sa.Column('best_weapon', sa.Integer(), nullable=True),
        sa.Column('best_weapon_level', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )

    op.create_table('match_user_stats',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('max_hp', sa.Integer(), nullable=True),
        sa.Column('hp_regen', sa.Float(), nullable=True),
        sa.Column('attack_power', sa.Integer(), nullable=True),
        sa.Column('attack_speed', sa.Float(), nullable=True),
        sa.Column('defense', sa.Integer(), nullable=True),
        sa.Column('skill_amp', sa.Integer(), nullable=True),
        sa.Column('move_speed', sa.Float(), nullable=True),
        sa.Column('ooc_move_speed', sa.Float(), nullable=True),
        sa.Column('sight_range', sa.Integer(), nullable=True),
        sa.Column('attack_range', sa.Float(), nullable=True),
        sa.Column('adaptive_force', sa.Float(), nullable=True),
        sa.Column('adaptive_force_attack', sa.Float(), nullable=True),
        sa.Column('adaptive_force_amp', sa.Float(), nullable=True),
        sa.Column('critical_strike_chance', sa.Float(), nullable=True),
        sa.Column('critical_damage', sa.Integer(), nullable=True),
        sa.Column('cooldown_reduction', sa.Integer(), nullable=True),
        sa.Column('life_steal', sa.Integer(), nullable=True),
        sa.Column('normal_life_steal', sa.Integer(), nullable=True),
        sa.Column('skill_life_steal', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )

    op.create_table('match_user_mmr',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('mmr_before', sa.Integer(), nullable=True),
        sa.Column('mmr_after', sa.Integer(), nullable=True),
        sa.Column('mmr_gain', sa.Integer(), nullable=True),
        sa.Column('mmr_gain_in_game', sa.Integer(), nullable=True),
        sa.Column('mmr_loss_entry_cost', sa.Integer(), nullable=True),
        sa.Column('rank_point', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )

    op.create_table('match_user_sight',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('sight_score', sa.Integer(), nullable=True),
        sa.Column('camera_setup', sa.Integer(), nullable=True),
        sa.Column('camera_remove', sa.Integer(), nullable=True),
        sa.Column('emp_drone_setup', sa.Integer(), nullable=True),
        sa.Column('basic_drone_setup', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num')
    )

    op.create_table('match_user_credit_acquisitions',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('acquisition_source_id', sa.Integer(), nullable=False),
        sa.Column('acquisition_type', sa.String(length=32), nullable=True),
        sa.Column('credit_amount', sa.Float(), nullable=True),
        sa.Column('source_category', sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(['acquisition_source_id'], ['credit_acquisition_source.source_id'], ),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num', 'acquisition_source_id')
    )

    op.create_table('match_user_credit_expenditures',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('expenditure_source_id', sa.Integer(), nullable=False),
        sa.Column('order_seq', sa.Integer(), nullable=False, comment='Purchase order in a single match for a user'),
        sa.Column('expenditure_type', sa.String(length=32), nullable=True),
        sa.Column('credit_amount', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['expenditure_source_id'], ['credit_expenditure_source.source_id'], ),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num', 'expenditure_source_id', 'order_seq')
    )

    op.create_table('match_user_credit_time',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('minute', sa.Integer(), nullable=False),
        sa.Column('used_credit', sa.Integer(), nullable=True),
        sa.Column('gain_credit', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num', 'minute')
    )

    op.create_table('match_user_object',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('user_num', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.String(length=32), nullable=False),
        sa.Column('metric_name', sa.String(length=32), nullable=False),
        sa.Column('value', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
        sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
        sa.PrimaryKeyConstraint('match_id', 'user_num', 'metric_type', 'metric_name')
    )


def downgrade() -> None:
    op.drop_table('match_user_object')
    op.drop_table('match_user_credit_time')
    op.drop_table('match_user_credit_expenditures')
    op.drop_table('match_user_credit_acquisitions')
    op.drop_table('match_user_sight')
    op.drop_table('match_user_mmr')
    op.drop_table('match_user_stats')
    op.drop_table('match_user_equipment')
    op.drop_table('match_user_damage')
    op.drop_table('match_user_trait')
    op.drop_table('match_user_combat')
    op.drop_table('match_user_end')
    op.drop_table('match_user_start')
    op.drop_table('match_team_info')
    op.drop_table('match_info')
    op.drop_table('credit_expenditure_source')
    op.drop_table('credit_acquisition_source')
    op.drop_table('tactical_skills')
    op.drop_table('weapon_types')
    op.drop_table('armor_types')
    op.drop_table('weather_info')
    op.drop_table('trait_info')
    op.drop_table('monster_info')
    op.drop_table('item_weapon')
    op.drop_table('item_armor')
    op.drop_table('installation_info')
    op.drop_table('character_levelup_stats')
    op.drop_table('character_info')
    op.drop_table('area_info')
    op.drop_index(op.f('ix_user_nickname'), table_name='user')
    op.drop_table('user')