# Eternal Return Crawler - 데이터 명세서

> **문서 버전**: v2.4 | **최종 수정**: 2026-03-16 | **대상 시즌**: Season 9
> **Schema 기준**: Alembic `38cbb6ad2222` (initial_schema)

---

## 목차
1. [개요](#개요)
2. [데이터베이스 ERD](#데이터베이스-erd)
3. [테이블 분류 및 구성](#테이블-분류-및-구성)
4. [메타 정보 테이블](#1-메타-정보-테이블)
5. [매치 데이터 테이블](#2-매치-데이터-테이블)
6. [Long Format 테이블](#3-long-format-테이블)
7. [데이터 수집 정책](#데이터-수집-정책)
8. [데이터 품질 및 주의사항](#데이터-품질-및-주의사항)
9. [활용 가이드](#활용-가이드)

---

## 개요

### 프로젝트 목적
이터널 리턴(Eternal Return) 게임의 공식 API를 통해 매치 데이터를 수집하고, 분석 가능한 형태로 정규화하여 MySQL 데이터베이스에 저장합니다.

### 데이터 소스
- **Eternal Return Open API**: `https://open-api.bser.io`
- **수집 대상**: 랭크(Rank) 매치만 수집 (`matching_mode = 3`)
- **수집 범위**: Top 1000 랭커로부터 시작하여 스노우볼 방식으로 확장

### 핵심 식별자

| 식별자 | 설명 | 특징 |
|--------|------|------|
| `match_id` | 매치 고유 ID | API의 `gameId`, BIGINT |
| `uid` | 유저 API 식별자 | VARCHAR(128), **닉네임 변경 시 함께 변경됨** |
| `user_num` | 내부 유저 ID | Auto Increment, FK로 사용 |
| `character_num` | 캐릭터 ID | `character_info.character_id`와 조인 |

> [!WARNING]
> **UID 불변성 주의**: 25년 11월 25일 이후 nickname 을 호출 할 때 마다, userId 는 다른 값을 반환 합니다. 즉, `uid`는 영구적이지 않으며, **유저가 닉네임을 변경할 때마다 uid도 변경**됩니다. 닉네임 변경 이전에 플레이한 경기는 신규 uid로 조회 시 포함되지 않습니다. 또한 API v1에서 `userNum` 기반 조회는 더 이상 지원되지 않으며, 모든 사용자 엔드포인트는 `uid`를 사용합니다.

---

## 데이터베이스 ERD

```mermaid
erDiagram
    user ||--o{ match_user_start : "user_num"
    match_info ||--o{ match_team_info : "match_id"
    match_team_info ||--o{ match_user_start : "match_id, team_number"
    match_user_start ||--o| match_user_end : "match_id, user_num"
    match_user_start ||--o| match_user_combat : "match_id, user_num"
    match_user_start ||--o| match_user_damage : "match_id, user_num"
    match_user_start ||--o| match_user_equipment : "match_id, user_num"
    match_user_start ||--o| match_user_stats : "match_id, user_num"
    match_user_start ||--o| match_user_mmr : "match_id, user_num"
    match_user_start ||--o| match_user_sight : "match_id, user_num"
    match_user_start ||--o{ match_user_trait : "match_id, user_num"
    match_user_start ||--o{ match_user_credit_acquisitions : "match_id, user_num"
    match_user_start ||--o{ match_user_credit_expenditures : "match_id, user_num"
    match_user_start ||--o{ match_user_credit_time : "match_id, user_num"
    match_user_start ||--o{ match_user_object : "match_id, user_num"
    match_user_start ||--o{ match_user_gadget : "match_id, user_num"

    match_info {
        bigint match_id PK
        int season_id
        datetime start_dtm
        int duration
    }
    
    user {
        int user_num PK
        varchar uid UK
        varchar nickname
        bigint last_match_id
    }
    
    match_user_start {
        bigint match_id PK
        int user_num PK
        int character_num
        int team_number
    }
```

---

## 테이블 분류 및 구성

| 분류 | 테이블 수 | 설명 |
|------|-----------|------|
| **메타 정보** | 12개 | 게임 정적 데이터 (버전별 관리) |
| **매치 데이터** | 12개 | 매치별 유저 데이터 (Wide Format) |
| **Long Format** | 6개 | 가변 개수 데이터 (정규화) |
| **소스 마스터** | 2개 | 크레딧 획득/소모 소스 룩업 테이블 |
| **합계** | **32개** | |

---

## 1. 메타 정보 테이블

### 버전 관리 체계
메타 정보는 게임 패치에 따라 변경될 수 있어 **버전별로 복합 키**를 사용합니다.

```
PK = (entity_id, season, major_version, minor_version)
```

> [!NOTE]
> 현재 수집 시 `minor_version = 0`으로 고정하여 메이저 패치 단위로 관리합니다.

---

### 1.1 user
유저 정보 및 크롤링 상태를 관리하는 핵심 테이블입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `user_num` | INT PK | 내부 유저 ID (Auto Increment) |
| `uid` | VARCHAR(128) UK | API 유저 식별자 |
| `nickname` | VARCHAR(30) | 현재 닉네임 |
| `last_match_id` | BIGINT | 마지막으로 수집한 매치 ID |
| `is_active` | BOOLEAN | 활성 유저 여부 |
| `last_updated_at` | DATETIME | 마지막 업데이트 시간 |

> [!TIP]
> `last_match_id`보다 큰 매치만 수집하여 중복을 방지합니다. `is_active = FALSE`인 유저는 탈퇴/휴면 계정으로 수집 대상에서 제외됩니다.

---

### 1.2 character_info
실험체(캐릭터) 기본 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `character_id` | INT PK | 캐릭터 ID |
| `season` | INT PK | 시즌 ID |
| `major_version` | INT | 메이저 패치 버전 |
| `minor_version` | INT | 마이너 패치 버전 |
| `character_name` | VARCHAR(255) | 캐릭터 이름 |
| `archetype_primary` | VARCHAR(255) | 주 역할군 |
| `archetype_secondary` | VARCHAR(255) | 부 역할군 |
| `weapon_range_type` | VARCHAR(255) | 원거리/근거리 타입 |
| `base_max_hp` | INT | 기본 최대 체력 |
| `base_attack_power` | INT | 기본 공격력 |
| `base_defense` | INT | 기본 방어력 |
| `base_skill_amp` | INT | 기본 스킬 증폭 |
| `base_hp_regen` | FLOAT | 기본 체력 재생 |
| `base_attack_speed` | FLOAT | 기본 공격 속도 |
| `base_move_speed` | FLOAT | 기본 이동 속도 |
| `base_sight_range` | FLOAT | 기본 시야 범위 |

---

### 1.3 item_weapon / item_armor
무기 및 방어구 아이템 정보입니다. 장비 분석 시 `match_user_equipment`와 조인합니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `item_id` | INT PK | 아이템 ID |
| `item_name` | VARCHAR(255) | 아이템 이름 |
| `item_grade` | VARCHAR(255) | 등급 (Uncommon/Rare/Epic/Legend/Mythic) |
| `weapon_type` / `armor_type` | VARCHAR(255) | 무기/방어구 타입 |
| `attack_power` | INT | 공격력 |
| `defense` | INT | 방어력 |
| `skill_amp` | INT | 스킬 증폭 |
| `max_hp` | INT | 최대 체력 |

### 1.4 기타 메타 테이블

| 테이블 | 설명 |
|--------|------|
| character_levelup_stats | 캐릭터 레벨업 당 스탯 증가량 |
| area_info | 지역 정보 |
| monster_info | 야생동물/에픽 몬스터 정보 |
| trait_info | 특성 정보 |
| weather_info | 날씨 정보 |
| installation_info | 설치물 정보 |
| weapon_types | 무기 타입 코드 매핑 |
| armor_types | 방어구 타입 코드 매핑 |
| tactical_skills | 전술 스킬 코드 매핑 |

---

## 2. 매치 데이터 테이블

### 2.1 match_info
매치의 기본 정보를 저장하는 최상위 테이블입니다.

| 컬럼 | 타입 | 설명 | 비고 |
|------|------|------|------|
| `match_id` | INT PK | 매치 고유 ID | API: `gameId`, index |
| `season_id` | INT | 시즌 ID | |
| `version_season` | INT | 시즌 | |
| `version_major` | INT | 메이저 패치 버전 | |
| `version_minor` | INT | 마이너 패치 버전 | |
| `matching_mode` | INT | 매칭 모드 | 3=랭크 |
| `matching_team_mode` | INT | 팀 모드 | 1=솔로, 2=듀오, 3=스쿼드 |
| `server_name` | VARCHAR(32) | 서버 이름 | |
| `match_size` | INT | 참가 인원 수 | `len(userGames)` (21명 또는 24명 고정) |
| `start_dtm` | DATETIME | 매치 시작 시간 | |
| `duration` | INT | 매치 진행 시간(초) | 최소 `totalTime` |
| `expired_tm` | DATETIME | 매치 만료 시간 | |
| `mmr_avg` | INT | 평균 MMR | |
| `main_weather` | INT | 메인 날씨 | |
| `sub_weather` | INT | 서브 날씨 | |
| `bot_added` | INT | 봇 추가 수 | |
| `bot_remain` | INT | 매치 종료 시점에 남아있는 봇의 수 | |
| `safe_areas` | INT | 안전 구역 수 | |
| `restricted_area_accelerated` | BOOLEAN | 금지구역 가속 여부 | |

---

### 2.2 match_team_info
팀 단위 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `match_id` | INT PK | 매치 ID (FK → match_info) |
| `team_number` | INT PK | 팀 번호 |
| `game_rank` | INT | 팀 순위 |
| `team_kill` | INT | 팀 킬 수 |
| `total_field_kill` | INT | 필드 킬 수 |
| `team_elimination` | INT | 팀 처치 수 |
| `team_down` | INT | 팀 처치 수 |
| `team_repeat_down` | INT | 팀 연속 처치 수 |
| `team_battle_zone_down` | INT | 팀 배틀존 처치 수 |
| `escape_state` | INT | 탈출 상태 |
| `team_down_cannot_eliminate` | INT | 사출방지 일자 처치 수 |
| `team_down_can_eliminate` | INT | 사출미방지 일자 처치 수 |
| `team_repeat_down_cannot_eliminate` | INT | 사출방지 일자 연속 처치 수 |
| `team_repeat_down_can_eliminate` | INT | 사출미방지 일자 연속 처치 수 |

---

### 2.3 match_user_start
**유저 매치의 중심 테이블**입니다. 모든 유저 관련 테이블이 이 테이블을 참조합니다.

| 컬럼 | 타입 | 설명 | 비고 |
|------|------|------|------|
| `match_id` | BIGINT PK | 매치 ID | FK → match_info |
| `user_num` | INT PK | 유저 내부 ID | FK → user |
| `nickname` | VARCHAR(128) | 매치 당시 닉네임 | |
| `character_num` | INT | 사용 캐릭터 ID | **INDEX** |
| `team_number` | INT | 팀 번호 | FK → match_team_info |
| `language` | VARCHAR(255) | 사용자 설정 언어 | |
| `skin_code` | INT | 스킨 코드 | |
| `premade` | BOOLEAN | 사전구성 팀 여부 | |
| `except_premade_team` | BOOLEAN | 비사전구성 팀 여부 | |
| `route_id_of_start` | INT | 시작 루트 ID | |
| `place_of_start` | INT | 시작 지역 | |
| `using_default_game_option` | BOOLEAN | 기본 설정 사용 여부 | |
| `premade_matching_type` | INT | 파티 매칭 타입 | |
| `tactical_skill_id` | INT | 전술 스킬 ID | **INDEX** |
| `ml_bot` | BOOLEAN | ML 봇 여부 | |

> [!IMPORTANT]
> `user_num`은 `uid`를 내부 정수 ID로 변환한 값입니다. 외부 조인 시 `user` 테이블을 통해 `uid`를 확인하세요.

---

### 2.4 match_user_end
매치 종료 시점의 유저 활동 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `victory` | BOOLEAN | 승리 여부 |
| `play_time` | INT | 플레이 시간(초) |
| `watch_time` | INT | 관전 시간(초) |
| `total_time` | INT | 총 시간(초) |
| `time_spent_in_briefing_room` | INT | 브리핑룸 체류 시간(초) |
| `craft_uncommon` ~ `craft_mythic` | INT | 등급별 제작 횟수 |
| `use_hyperloop` | INT | 하이퍼루프 사용 횟수 |
| `use_security_console` | INT | 보안 콘솔 사용 횟수 |
| `break_count` | INT | 사출방지 일자 팀 전멸시킨 횟수 |
| `enter_dimension_rift` | INT | 차원 균열 진입 횟수 |
| `enter_dimension_empowered_rift` | INT | 강화 차원 균열 진입 횟수 |
| `win_dimension_rift` | INT | 차원 균열 승리 횟수 |
| `win_dimension_empowered_rift` | INT | 강화 차원 균열 승리 횟수 |
| `resurrectionkit_count` | INT | 부활 횟수 |
| `resurrectionkit_credit_count` | INT | 크레딧 부활 횟수 |
| `fishing_count` | INT | 낚시 횟수 |
| `emoticon_count` | INT | 이모티콘 사용 횟수 |
| `used_pairloop` | INT | 루프 사용 횟수 |
| `give_up` | BOOLEAN | 포기 여부 |
| `team_spectator` | INT | 팀 관전 횟수 |
| `is_leaving_before_credit_revival_terminate` | BOOLEAN | 크레딧 부활 전 이탈 여부 |

---

### 2.5 match_user_combat
전투 관련 통계입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `character_level` | INT | 최종 캐릭터 레벨 |
| `tactical_skill_level` | INT | 전술 스킬 레벨 |
| `player_kill` | INT | 플레이어 킬 수 |
| `player_assistant` | INT | 어시스트 수 |
| `player_deaths` | INT | 사망 수 |
| `monster_kill` | INT | 몬스터 킬 수 |
| `kills_phase_one` ~ `kills_phase_three` | INT | 페이즈별 킬 수 |
| `deaths_phase_one` ~ `deaths_phase_three` | INT | 페이즈별 사망 수 |
| `terminate_count` | INT | 팀 전원 처치 횟수 |
| `terminate_count_cannot_eliminate` | INT | 사출방지 일자 팀 전멸 횟수 |
| `clutch_count` | INT | 클러치 횟수 |
| `unknown_kill` | INT | 원인 불명 킬 수 |
| `cc_time_to_player` | FLOAT | CC기 적중 시간 |
| `credit_revival_count` | INT | 크레딧 부활 횟수 |
| `credit_revived_others_count` | INT | 타인 크레딧 부활 횟수 |
| `reunited_count` | INT | 팀원 모두 부활 시킨 횟수 |
| `tactical_skill_count` | INT | 전술 스킬 사용 횟수 |

---

### 2.6 match_user_damage
데미지 상세 정보입니다. **데미지 유형별로 세분화**되어 있습니다.

| 컬럼 그룹 | 설명 |
|-----------|------|
| `damage_to_player_*` | 플레이어에게 가한 데미지 |
| `damage_from_player_*` | 플레이어로부터 받은 데미지 |
| `damage_to_monster_*` | 몬스터에게 가한 데미지 |
| `damage_from_monster_total` | 몬스터로부터 받은 총 데미지 |

**데미지 유형 접미사** (`to_player`, `from_player`, `to_monster` 공통):
- `_total`: 총 데미지
- `_basic`: 기본 공격
- `_skill`: 스킬
- `_item_skill`: 아이템 스킬
- `_direct`: 고정 데미지
- `_trap`: 트랩
- `_unique_skill`: 고유 스킬

**`to_player` 전용 접미사**:
- `_shield`: 보호막 데미지

| 추가 컬럼 | 설명 |
|-----------|------|
| `damage_offseted_by_shield_player` | 보호막으로 상쇄된 플레이어 데미지 |
| `damage_offseted_by_shield_monster` | 보호막으로 상쇄된 몬스터 데미지 |
| `damage_to_guide_robot` | 가이드 로봇(루미)에게 가한 데미지 |
| `heal_amount` | 힐량 |
| `team_recover` | 팀 회복량 |
| `protect_absorb` | 보호막 흡수량 |

---

### 2.7 match_user_equipment
장비 정보입니다.

| 컬럼 | 설명 |
|------|------|
| `first_weapon` ~ `first_leg` | **첫 완성** 장비 (무기/옷/머리/팔(장식)/다리) |
| `last_weapon` ~ `last_leg` | **최종** 장비 |
| `best_weapon` | 가장 높은 등급 무기 |
| `best_weapon_level` | 가장 높은 무기 레벨 |

> [!TIP]
> 장비 ID는 item_weapon, item_armor 테이블과 조인하여 아이템 이름 및 스탯을 확인할 수 있습니다.

---

### 2.8 match_user_stats
매치 종료 시점의 유저 최종 스탯입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `max_hp` | INT | 최대 체력 |
| `hp_regen` | FLOAT | 체력 재생 |
| `attack_power` | INT | 공격력 |
| `attack_speed` | FLOAT | 공격 속도 |
| `defense` | INT | 방어력 |
| `skill_amp` | INT | 스킬 증폭 |
| `move_speed` | FLOAT | 이동 속도 |
| `ooc_move_speed` | FLOAT | 비전투 이동 속도 |
| `sight_range` | INT | 시야 범위 |
| `attack_range` | FLOAT | 공격 사거리 |
| `adaptive_force` | FLOAT | 적응형 능력치 |
| `adaptive_force_attack` | FLOAT | 적응형 공격력 |
| `adaptive_force_amp` | FLOAT | 적응형 스킬 증폭 |
| `critical_strike_chance` | FLOAT | 치명타 확률 |
| `critical_damage` | INT | 치명타 데미지 |
| `cooldown_reduction` | INT | 쿨다운 감소 |
| `life_steal` | INT | 생명력 흡수 |
| `normal_life_steal` | INT | 일반 공격 흡혈 |
| `skill_life_steal` | INT | 스킬 흡혈 |

---

### 2.9 match_user_mmr
MMR 변동 정보입니다.

| 컬럼 | 설명 |
|------|------|
| `mmr_before` | 매치 전 MMR |
| `mmr_after` | 매치 후 MMR |
| `mmr_gain` | MMR 변동량 |
| `mmr_gain_in_game` | 인게임 획득 MMR |
| `mmr_loss_entry_cost` | 참가 비용 |
| `rank_point` | 랭크 포인트 |

---

### 2.10 match_user_sight
시야 및 정찰 관련 정보입니다.

| 컬럼 | API 필드 | 설명 |
|------|----------|------|
| `sight_score` | `viewContribution` | 시야 기여도 점수 |
| `camera_setup` | `addTelephotoCamera` | 망원 카메라 설치 횟수 |
| `camera_remove` | `removeTelephotoCamera` | 망원 카메라 제거 횟수 |
| `emp_drone_setup` | `useEmpDrone` | EMP 드론 사용 횟수 |
| `basic_drone_setup` | `useReconDrone` | 정찰 드론 사용 횟수 |

> [!NOTE]
> 감시 카메라(`addSurveillanceCamera`, `removeSurveillanceCamera`)는 망원 카메라와 별개의 아이템으로 현재 모든 값이 0으로 고정되어 있습니다. 

---

## 3. Long Format 테이블

가변 개수의 데이터를 정규화하여 저장합니다.

### 3.1 match_user_trait
유저가 선택한 특성 정보입니다. 한 유저당 여러 행이 존재합니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `match_id` | BIGINT PK | 매치 ID |
| `user_num` | INT PK | 유저 ID |
| `trait_id` | INT PK | 특성 ID |
| `trait_type` | VARCHAR(20) | 특성 타입 (`first_core`, `first_sub`, `second_sub`) |

> [!NOTE]
> - `traitFirstCore` (API): 단일 정수값 → `trait_type = 'first_core'`로 1행 저장
> - `traitFirstSub` (API): 정수 배열 → `trait_type = 'first_sub'`로 각 원소당 1행 저장
> - `traitSecondSub` (API): 정수 배열 → `trait_type = 'second_sub'`로 각 원소당 1행 저장

---

### 3.2 match_user_credit_acquisitions
크레딧 획득 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `match_id` | BIGINT PK | 매치 ID |
| `user_num` | INT PK | 유저 ID |
| `acquisition_source_id` | INT PK | 획득 소스 ID (FK) |
| `acquisition_type` | VARCHAR(32) | 획득 유형 |
| `credit_amount` | FLOAT | 획득 금액 |
| `source_category` | VARCHAR(32) | 소스 카테고리 |

**획득 소스 카테고리**:
| 카테고리 | 설명 | 예시 |
|----------|------|------|
| monster | 야생동물/에픽 몬스터 | KillChicken, KillAlpha |
| player | 플레이어 처치 | KillPlayerMerge, KillAssistDivideContribute |
| env | 환경 요소 | GoldSecurityConsoleAccess, KillOrb |
| timebased | 시간 기반 보상 | TimeElapsedCompensationByMiliSecond |
| bounty | 현상금 | ItemBounty |
| special | 특수 | GetBySkill, TraitSkillCoinToss |

---

### 3.3 match_user_credit_expenditures
크레딧 소모(구매) 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `match_id` | BIGINT PK | 매치 ID |
| `user_num` | INT PK | 유저 ID |
| `event_seq` | INT PK | 구매 순서 |
| `expenditure_source_id` | INT FK | 소모 소스 ID |
| `expenditure_type` | VARCHAR(32) | 소모 유형 |
| `item_code` | INT | 아이템 코드 (있는 경우) |
| `credit_amount` | INT | 소모 금액 |

---

### 3.4 match_user_credit_time
분당 크레딧 획득/소모 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `minute` | INT PK | 분 (0-19) |
| `used_credit` | INT | 해당 분에 소모한 크레딧 |
| `gain_credit` | INT | 해당 분에 획득한 크레딧 |

---

### 3.5 match_user_object
오브젝트/에픽 몬스터 상호작용 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `metric_type` | VARCHAR(32) PK | 메트릭 유형 |
| `metric_name` | VARCHAR(32) PK | 메트릭 이름 |
| `value` | INT | 값 |

**메트릭 유형**:
| metric_type | metric_name 예시 | 설명 |
|-------------|-----------------|------|
| kill_monster | total_kill_monster | 총 몬스터 킬 |
| get_cube | get_cube_red, get_cube_gold 등 | 버프 큐브 획득 |
| kill_alpha, kill_omega 등 | - | 에픽 몬스터 처치 |
| collect_tree_of_life | - | 생명의 나무 수집 |

---

### 3.6 credit_acquisition_source / credit_expenditure_source
크레딧 획득/소모 소스의 마스터(룩업) 테이블입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `source_id` | INT PK | 소스 ID (Auto Increment) |
| `source_name` | VARCHAR(64) UK | 소스 이름 |

> [!NOTE]
> `match_user_credit_acquisitions.acquisition_source_id` → `credit_acquisition_source.source_id`
> `match_user_credit_expenditures.expenditure_source_id` → `credit_expenditure_source.source_id`

---

### 3.7 match_user_gadget
가젯 사용 정보입니다.

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `gadget_id` | INT PK | 가젯 ID |
| `gadget_count` | INT | 사용 횟수 |

---

## 데이터 수집 정책

### 수집 대상
| 항목 | 값 |
|------|-----|
| 매칭 모드 | 랭크 (`matching_mode = 3`) |
| 서버 | 한국 (`server_code = 10`) |
| 시즌 | 현재 시즌 (config로 설정) |

### 스노우볼 수집 방식
```mermaid
flowchart LR
    A[Top 1000 랭커] --> B[시드 유저 등록]
    B --> C[유저별 매치 수집]
    C --> D[매치 내 신규 유저 발견]
    D --> E[신규 유저 등록]
    E --> C
```

### 중복 방지 메커니즘
1. `user.last_match_id`보다 큰 매치만 수집
2. check_match_exists()로 이미 수집된 매치 ID 필터링
3. Upsert 방식으로 중복 삽입 방지 (`ON DUPLICATE KEY UPDATE`)

---

## 데이터 품질 및 주의사항

> [!WARNING]
> ### 알려진 제한사항
> 1. **탈퇴/휴면 유저**: API에서 404 반환 시 `is_active = FALSE`로 설정
> 2. **닉네임 변경**: 매치 당시 닉네임과 현재 닉네임이 다를 수 있음
> 3. **버전 변경**: 패치 후 아이템/캐릭터 스탯 변경 시 버전별 조인 필요

### NULL 처리
- 대부분의 통계 컬럼은 API 응답에 없을 경우 `0` 또는 `NULL`
- 선택적 필드는 기본값 `0`으로 처리

### 시간대
- `start_dtm`: UTC 기준으로 저장
- 분석 시 한국 시간(KST, UTC+9) 변환 필요

---

## 활용 가이드

### 자주 사용하는 조인 패턴

#### 캐릭터별 승률 분석
```sql
SELECT 
    ci.character_name,
    COUNT(*) as games,
    SUM(CASE WHEN ue.victory THEN 1 ELSE 0 END) / COUNT(*) as win_rate
FROM match_user_start us
JOIN match_user_end ue ON us.match_id = ue.match_id AND us.user_num = ue.user_num
JOIN character_info ci ON us.character_num = ci.character_id
WHERE ci.season = 9
GROUP BY ci.character_name
ORDER BY games DESC;
```

#### 유저별 최근 매치 조회
```sql
SELECT 
    u.nickname,
    mi.start_dtm,
    uc.player_kill,
    uc.player_assistant,
    mti.game_rank
FROM user u
JOIN match_user_start us ON u.user_num = us.user_num
JOIN match_info mi ON us.match_id = mi.match_id
JOIN match_user_combat uc ON us.match_id = uc.match_id AND us.user_num = uc.user_num
JOIN match_team_info mti ON us.match_id = mti.match_id AND us.team_number = mti.team_number
WHERE u.nickname = 'TARGET_NICKNAME'
ORDER BY mi.start_dtm DESC
LIMIT 10;
```

### 성능 최적화 팁
1. `match_info.start_dtm`에 인덱스가 있으므로 날짜 범위 필터링 활용
2. `character_num`, `tactical_skill_id`에 인덱스가 있으므로 해당 컬럼으로 필터링 권장
3. Long Format 테이블은 레코드 수가 많으므로 필요한 경우만 조인

---

---

## 원본 API 응답 구조 (참고용)

실제 API 응답은 아래 구조를 따르며, **현재 수집하지 않는 필드**도 포함되어 있습니다.

### 수집되지 않는 주요 필드

> [!IMPORTANT]
> 아래 필드들은 API에서 제공되지만 현재 DB 스키마에 포함되지 않습니다. 추후 분석 필요 시 스키마 확장을 고려하세요.

#### 스킬 및 마스터리 정보

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `masteryLevel` | Object | 무기/방어구 마스터리 레벨 | `{"1": 16, "201": 17, "202": 13}` |
| `skillLevelInfo` | Object | 스킬별 레벨 | `{"1033200": 5, "1033300": 4}` |
| `skillOrderInfo` | Object | 스킬 찍은 순서 | `{"1": 1033200, "2": 1033300}` |

> **마스터리 코드 해석**:
> - `1-24`: 무기 마스터리 (1=글러브, 2=양손검 등)
> - `101-103`: 생존 마스터리 (사냥, 탐색, 이동)
> - `201-202`: 제작 마스터리 (장비, 음식)

#### 전투 상세 정보

| 필드 | 타입 | 설명 |
|------|------|------|
| `killMonsters` | Object | 몬스터 종류별 킬 수 | `{"1": 7, "4": 10}` |
| `killDetails` | String (JSON) | 상세 킬 정보 | `"{\"78\":1,\"18\":1}"` |
| `deathDetails` | String (JSON) | 상세 사망 정보 | |
| `killerUserNum` ~ `killerUserNum3` | INT | 처치한 유저 ID (최대 3명) |
| `killer` ~ `killer3` | String | 처치자 유형 (player/monster) |
| `causeOfDeath` ~ `causeOfDeath3` | String | 사망 원인 스킬명 |
| `killerCharacter` ~ `killerCharacter3` | String | 처치자 캐릭터명 |
| `killerWeapon` ~ `killerWeapon3` | String | 처치자 무기 타입 |

#### 배틀존 정보

| 필드 | 타입 | 설명 |
|------|------|------|
| `battleZone1AreaCode` ~ `battleZone3AreaCode` | INT | 배틀존 지역 코드 |
| `battleZone1BattleMark` ~ `battleZone3BattleMark` | INT | 배틀존 마크 |
| `battleZone1ItemCode` ~ `battleZone3ItemCode` | Array | 배틀존 획득 아이템 |
| `battleZone1Winner` ~ `battleZone3Winner` | BOOLEAN | 배틀존 승리 여부 |
| `battleZonePlayerKill` | INT | 배틀존 내 킬 수 |
| `battleZoneDeaths` | INT | 배틀존 내 사망 수 |

#### 음식 및 아이템 수집

| 필드 | 타입 | 설명 | 비고 |
|------|------|------|------|
| `foodCraftCount` | Array[7] | 음식 등급별 제작 횟수 | 0-6: 등급 |
| `beverageCraftCount` | Object | 등급별 음료 제작 횟수 | |
| `airSupplyOpenCount` | Object | 공중 보급 상자 개봉 횟수 | 보급 등급별 |
| `collectItemForLog` | Array[10] | 수집품 수집 횟수 | CollectibleCode 인덱스 |
| `itemTransferredConsole` | Array | 전송 콘솔로 요청한 아이템 코드 목록 | |
| `itemTransferredDrone` | Array | 전송 드론으로 요청한 아이템 코드 목록 | |
| `boughtInfusion` | String (JSON) | 구매한 인퓨전 | **[COBALT 전용]** |
| `finalInfusion` | int[3] | 최종 보유 특성 인퓨전 3개 | **[COBALT 전용]** |

#### 스탯 미수집 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `maxSp` | INT | 최대 SP |
| `spRegen` | FLOAT | SP 재생 |
| `amplifierToMonster` | FLOAT | 몬스터 대상 증폭 |
| `trapDamage` | FLOAT | 트랩 데미지 |

#### 경험치 관련 미수집 필드

| 필드 | 타입 | 설명 | 비고 |
|------|------|------|------|
| `gainExp` | INT | 매치 종료 후 계정이 획득한 경험치 | PDF 공식 정의 |
| `baseExp` | INT | 기본 경험치 | 실제 데이터에만 존재 |
| `bonusExp` | INT | 보너스 경험치 | 실제 데이터에만 존재 |
| `bonusCoin` | INT | 보너스 코인 | 실제 데이터에만 존재 |

#### MMR 관련 미수집 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `gainedNormalMmrKFactor` | FLOAT | 일반 MMR K-factor (**Deprecated** - 더 이상 지원되지 않음) |

#### 전투 상세 미수집 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `totalDoubleKill` | INT | 더블킬 횟수 |
| `totalTripleKill` | INT | 트리플킬 횟수 |
| `totalQuadraKill` | INT | 쿼드라킬 횟수 |
| `totalExtraKill` | INT | 5킬 이상 연속킬 횟수 |

#### 크레딧 상세 미수집 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `activelyGainedCredits` | INT | 자동 획득 크레딧 합계 |
| `sumUsedVFCredits` | INT | 크레딧 소모 합계 |
| `totalGainVFCredit` | INT | 크레딧 총 획득량 |
| `killPlayerGainVFCredit` | INT | 플레이어 처치 크레딧 |
| `killChickenGainVFCredit` | INT | 닭 처치 크레딧 |
| `killBoarGainVFCredit` | INT | 멧돼지 처치 크레딧 |
| `killWildDogGainVFCredit` | INT | 들개 처치 크레딧 |
| `killWolfGainVFCredit` | INT | 늑대 처치 크레딧 |
| `killBearGainVFCredit` | INT | 곰 처치 크레딧 |
| `killOmegaGainVFCredit` | INT | 오메가 처치 크레딧 |
| `killBatGainVFCredit` | INT | 박쥐 처치 크레딧 |
| `killWicklineGainVFCredit` | INT | 위클라인 처치 크레딧 |
| `killAlphaGainVFCredit` | INT | 알파 처치 크레딧 |
| `killGammaGainVFCredit` | INT | 감마 처치 크레딧 |
| `killItemBountyGainVFCredit` | INT | 현상금 아이템 크레딧 |
| `killDroneGainVFCredit` | INT | 드론 처치 크레딧 |
| `killTurretGainVFCredit` | INT | 터렛 처치 크레딧 |
| `itemShredderGainVFCredit` | INT | 아이템 분쇄 크레딧 |
| `remoteDroneUseVFCreditMySelf` | INT | 원격 드론(자신) 크레딧 소모 |
| `remoteDroneUseVFCreditAlly` | INT | 원격 드론(아군) 크레딧 소모 |
| `kioskFromMaterialUseVFCredit` | INT | 키오스크 재료 크레딧 소모 (`transferConsoleFromMaterialUseVFCredit`) |
| `kioskFromEscapeKeyUseVFCredit` | INT | 키오스크 탈출 키트 크레딧 소모 (`transferConsoleFromEscapeKeyUseVFCredit`) |
| `kioskFromRevivalUseVFCredit` | INT | 키오스크 부활 크레딧 소모 (`transferConsoleFromRevivalUseVFCredit`) |
| `tacticalSkillUpgradeUseVFCredit` | INT | 전술 스킬 업그레이드 크레딧 소모 |
| `infusionReRollUseVFCredit` | INT | 인퓨전 리롤 크레딧 소모(**[COBALT 전용]**) |
| `infusionTraitUseVFCredit` | INT | 인퓨전 특성 크레딧 소모(**[COBALT 전용]**) |
| `infusionRelicUseVFCredit` | INT | 인퓨전 유물 크레딧 소모(**[COBALT 전용]**) |
| `infusionStoreUseVFCredit` | INT | 인퓨전 상점 크레딧 소모(**[COBALT 전용]**) |
| `crGetPhaseStart` | INT | 매치 시작시 제공되는 크레딧 |

#### 아이템/제작 미수집 필드

| 필드 | 타입 | 설명 | 비고 |
|------|------|------|------|
| `campFireCraftUncommon` | INT | Uncommon 음식 제작 횟수 | |
| `campFireCraftRare` | INT | Rare 음식 제작 횟수 | |
| `campFireCraftEpic` | INT | Epic 음식 제작 횟수 | |
| `campFireCraftLegendary` | INT | Legendary 음식 제작 횟수 | |
| `usedNormalHealPack` | INT | 일반 회복 팩 사용량 | **[COBALT 전용]** |
| `usedReinforcedHealPack` | INT | 강화 회복 팩 사용량 | **[COBALT 전용]** |
| `usedNormalShieldPack` | INT | 일반 보호막 팩 사용량 (`usedNormalShiedPack`) | **[COBALT 전용]** |
| `usedReinforcedShieldPack` | INT | 강화 보호막 팩 사용량 | **[COBALT 전용]** |
| `StartingItems` | int[7] | 초기 획득 아이템 세트 (보통 6개) | **[COBALT 전용]** |

#### 시야 미수집 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `addSurveillanceCamera` | INT | 감시 카메라 설치 횟수 |
| `removeSurveillanceCamera` | INT | 감시 카메라 제거 횟수 |

#### 가이드 로봇(루미) 미수집 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `useGuideRobot` | INT | 루미 사용 횟수 |
| `guideRobotRadial` | INT | 루미에서 Radial 등급 아이템 구매 크레딧 |
| `guideRobotFlagShip` | INT | 루미에서 FlagShip 등급 아이템 구매 크레딧 |
| `guideRobotSignature` | INT | 루미에서 Signature 등급 아이템 구매 크레딧 |

#### 전투 상세 미수집 필드 (COBALT 전용)

| 필드 | 타입 | 설명 |
|------|------|------|
| `killsPhaseOne` | INT | 페이즈 1 처치 수 |
| `killsPhaseTwo` | INT | 페이즈 2 처치 수 |
| `killsPhaseThree` | INT | 페이즈 3 처치 수 |
| `deathsPhaseOne` | INT | 페이즈 1 사망 수 |
| `deathsPhaseTwo` | INT | 페이즈 2 사망 수 |
| `deathsPhaseThree` | INT | 페이즈 3 사망 수 |

> [!NOTE]
> 현재 스펙에서 `kills_phase_one` 등은 DB에 수집됩니다. PDF에 따르면 이 필드들은 **[COBALT 전용]**이지만 실제 랭크 매치 데이터에도 존재하는 것으로 확인됩니다.

#### 기타 미수집 필드

| 필드 | 타입 | 설명 | 비고 |
|------|------|------|------|
| `totalTKPerMin` | Array[20] | 분당 팀 킬 수 | |
| `scoredPoint` | Array[20] | 분당 점수 포인트 | **[COBALT 전용]** |
| `squadRumbleRank` | INT | 스쿼드 럼블 순위 | **[스쿼드 럼블 전용]** |
| `accountLevel` | INT | 계정 레벨 | |
| `survivableTime` | INT | 생존 가능 시간 | |
| `getBoriReward` | Object | 보리 처치 시 드롭 상자 등급 및 횟수 | |
| `activeInstallation` | Object | 게임에서 사용된 환경변수 사용 횟수 | `{"4": 5, "1": 1}` |
| `equipmentGrade` | Object | 장비 등급 | `{"0": 5, "1": 5}` |
| `sumGetBuffCube` | INT | 큐브 총 획득 수 | |
| `routeSlotId` | INT | 선택한 경로의 슬롯 ID | |
| `totalTurbineTakeOver` | INT | 증폭기 점령 성공 횟수 | **[COBALT 전용]** |
| `enterTurbulentRift` | INT | 난류 진입 횟수 | |
| `killGamma` | BOOLEAN | 감마 처치 여부 (처치자만) | |
| `cobaltRandomPickRemoveCharacter` | INT | 무작위 선택에서 제거한 캐릭터 코드 | **[COBALT 전용]** |
| `afkDtm` | DATETIME | 자리 비움 시간 | |
| `giveupDtm` | DATETIME | 포기 시간 | |
| `killDetails` | Object | 처치한 캐릭터별 횟수 딕셔너리 | `<캐릭터코드, 횟수>` |
| `deathDetails` | Object | 처치당한 캐릭터별 횟수 딕셔너리 | `<캐릭터코드, 횟수>` |

#### Deprecated 필드 (battleZone 관련)

> [!WARNING]
> 아래 필드들은 API 공식 문서에서 **사용 중단(Deprecated)**으로 표시되었습니다.

| 필드 | 비고 |
|------|------|
| `battleZone1/2/3AreaCode` | Deprecated |
| `battleZone1/2/3BattleMark` | Deprecated |
| `battleZone1/2/3ItemCode` | Deprecated |
| `battleZone1/2/3Winner` | Deprecated |
| `battleZone1/2/3BattleMarkCount` | Deprecated |
| `battleZonePlayerKillCount` | Deprecated (`battleZonePlayerKill`로 데이터 내 존재) |
| `battleZonePlayerDeathCount` | Deprecated |
| `battleZoneDeaths` | Deprecated |
| `teamDownInAutoResurrection` | Deprecated |
| `teamDownDeactiveAutoResurrection` | Deprecated |
| `teamRepeatDownInAutoResurrection` | Deprecated |
| `teamRepeatDownDeactiveAutoResurrection` | Deprecated |

#### 레거시 필드 (Deprecated, 데이터는 반환되나 해석 방법 미지원)

| 필드 | 설명 |
|------|------|
| `killerUserNum` / `killerUserNum2` / `killerUserNum3` | 처치자 userNum (레거시) |
| `killer` / `killer2` / `killer3` | 처치 주체 식별자 (레거시) |
| `killDetail` / `killDetail2` / `killDetail3` | 처치자 닉네임 (레거시) |
| `causeOfDeath` / `causeOfDeath2` / `causeOfDeath3` | 사망 원인 스킬명 (레거시) |
| `placeOfDeath` / `placeOfDeath2` / `placeOfDeath3` | 사망 지역 ID (레거시) |
| `killerCharacter` / `killerCharacter2` / `killerCharacter3` | 처치자 캐릭터명 (레거시) |
| `killerWeapon` / `killerWeapon2` / `killerWeapon3` | 처치자 무기 (레거시) |

---

### 크레딧 관련 상세 필드
#### 크레딧 획득 상세 (`creditSource` 대응)

| 필드 | 설명 |
|------|------|
| `crGetAnimal` | 일반 동물 처치 획득 |
| `crGetMutant` | 변이 동물 처치 획득 |
| `crGetKill` | 플레이어 처치 획득 |
| `crGetAssist` | 어시스트 획득 |
| `crGetTimeElapsed` | 시간 경과 획득 |
| `crGetCreditBonus` | 보너스 크레딧 |
| `crGetByGuideRobot` | 가이드 로봇 획득 (루미) |

#### 크레딧 소모 상세

| 필드 | 설명 |
|------|------|
| `crUseRemoteDrone` | 원격 드론 사용 |
| `crUseTreeOfLife` | 생명의 나무 사용 |
| `crUseMeteorite` | 운석 사용 |
| `crUseMythril` | 미스릴 사용 |
| `crUseForceCore` | 포스코어 사용 |
| `crUseVFBloodSample` | VF 혈액 샘플 사용 |
| `crUseActivationModule` | 전술 스킬 업그레이드 사용 |
| `crUseRootkit` | 루트킷 사용 |

---

### API 필드-DB 컬럼 매핑 표

| API 필드 | DB 컬럼 | 테이블 |
|----------|---------|--------|
| `gameId` | `match_id` | match_info |
| `seasonId` | `season_id` | match_info |
| `versionSeason` | `version_season` | match_info |
| `versionMajor` | `version_major` | match_info |
| `versionMinor` | `version_minor` | match_info |
| `startDtm` | `start_dtm` | match_info |
| `duration` | `duration` | match_info |
| `matchSize` | `match_size` | match_info |
| `mmrAvg` | `mmr_avg` | match_info |
| `mainWeather` | `main_weather` | match_info |
| `subWeather` | `sub_weather` | match_info |
| `botAdded` | `bot_added` | match_info |
| `botRemain` | `bot_remain` | match_info |
| `safeAreas` | `safe_areas` | match_info |
| `restrictedAreaAccelerated` | `restricted_area_accelerated` | match_info |
| `serverName` | `server_name` | match_info |
| `matchingMode` | `matching_mode` | match_info |
| `matchingTeamMode` | `matching_team_mode` | match_info |
| `expireDtm` | `expired_tm` | match_info |
| `teamNumber` → 팀 단위 집계 | `game_rank`, `team_kill` 등 | match_team_info |
| `escapeState` | `escape_state` | match_team_info |
| `teamKill` | `team_kill` | match_team_info |
| `totalFieldKill` | `total_field_kill` | match_team_info |
| `teamElimination` | `team_elimination` | match_team_info |
| `teamDown` | `team_down` | match_team_info |
| `teamRepeatDown` | `team_repeat_down` | match_team_info |
| `teamBattleZoneDown` | `team_battle_zone_down` | match_team_info |
| `teamDownCanNotEliminate` | `team_down_cannot_eliminate` | match_team_info |
| `teamDownCanEliminate` | `team_down_can_eliminate` | match_team_info |
| `teamRepeatDownCanNotEliminate` | `team_repeat_down_cannot_eliminate` | match_team_info |
| `teamRepeatDownCanEliminate` | `team_repeat_down_can_eliminate` | match_team_info |
| `characterNum` | `character_num` | match_user_start |
| `preMade` | `premade` | match_user_start |
| `tacticalSkillGroup` | `tactical_skill_id` | match_user_start |
| `mlbot` | `ml_bot` | match_user_start |
| `skinCode` | `skin_code` | match_user_start |
| `language` | `language` | match_user_start |
| `routeIdOfStart` | `route_id_of_start` | match_user_start |
| `placeOfStart` | `place_of_start` | match_user_start |
| `usingDefaultGameOption` | `using_default_game_option` | match_user_start |
| `premadeMatchingType` | `premade_matching_type` | match_user_start |
| `exceptPreMadeTeam` | `except_premade_team` | match_user_start |
| `victory` | `victory` | match_user_end |
| `playTime` | `play_time` | match_user_end |
| `watchTime` | `watch_time` | match_user_end |
| `totalTime` | `total_time` | match_user_end |
| `timeSpentInBriefingRoom` | `time_spent_in_briefing_room` | match_user_end |
| `craftUncommon` ~ `craftMythic` | `craft_uncommon` ~ `craft_mythic` | match_user_end |
| `useHyperLoop` | `use_hyperloop` | match_user_end |
| `useSecurityConsole` | `use_security_console` | match_user_end |
| `breakCount` | `break_count` | match_user_end |
| `enterDimensionRift` | `enter_dimension_rift` | match_user_end |
| `enterDimensionEmpoweredRift` | `enter_dimension_empowered_rift` | match_user_end |
| `winFromDimensionRift` | `win_dimension_rift` | match_user_end |
| `winFromDimensionEmpoweredRift` | `win_dimension_empowered_rift` | match_user_end |
| `resurrectionKitUsageCount` | `resurrectionkit_count` | match_user_end |
| `resurrectionKitToCredit` | `resurrectionkit_credit_count` | match_user_end |
| `fishingCount` | `fishing_count` | match_user_end |
| `useEmoticonCount` | `emoticon_count` | match_user_end |
| `usedPairLoop` | `used_pairloop` | match_user_end |
| `giveUp` | `give_up` | match_user_end |
| `teamSpectator` | `team_spectator` | match_user_end |
| `isLeavingBeforeCreditRevivalTerminate` | `is_leaving_before_credit_revival_terminate` | match_user_end |
| `playerKill` | `player_kill` | match_user_combat |
| `playerAssistant` | `player_assistant` | match_user_combat |
| `playerDeaths` | `player_deaths` | match_user_combat |
| `monsterKill` | `monster_kill` | match_user_combat |
| `characterLevel` | `character_level` | match_user_combat |
| `tacticalSkillLevel` | `tactical_skill_level` | match_user_combat |
| `killsPhaseOne` ~ `killsPhaseThree` | `kills_phase_one` ~ `kills_phase_three` | match_user_combat |
| `deathsPhaseOne` ~ `deathsPhaseThree` | `deaths_phase_one` ~ `deaths_phase_three` | match_user_combat |
| `terminateCount` | `terminate_count` | match_user_combat |
| `terminateCountCanNotEliminate` | `terminate_count_cannot_eliminate` | match_user_combat |
| `clutchCount` | `clutch_count` | match_user_combat |
| `unknownKill` | `unknown_kill` | match_user_combat |
| `ccTimeToPlayer` | `cc_time_to_player` | match_user_combat |
| `creditRevivalCount` | `credit_revival_count` | match_user_combat |
| `creditRevivedOthersCount` | `credit_revived_others_count` | match_user_combat |
| `reunitedCount` | `reunited_count` | match_user_combat |
| `tacticalSkillUseCount` | `tactical_skill_count` | match_user_combat |
| `maxHp` | `max_hp` | match_user_stats |
| `hpRegen` | `hp_regen` | match_user_stats |
| `attackPower` | `attack_power` | match_user_stats |
| `attackSpeed` | `attack_speed` | match_user_stats |
| `defense` | `defense` | match_user_stats |
| `skillAmp` | `skill_amp` | match_user_stats |
| `moveSpeed` | `move_speed` | match_user_stats |
| `outOfCombatMoveSpeed` | `ooc_move_speed` | match_user_stats |
| `sightRange` | `sight_range` | match_user_stats |
| `attackRange` | `attack_range` | match_user_stats |
| `adaptiveForce` | `adaptive_force` | match_user_stats |
| `adaptiveForceAttack` | `adaptive_force_attack` | match_user_stats |
| `adaptiveForceAmplify` | `adaptive_force_amp` | match_user_stats |
| `criticalStrikeChance` | `critical_strike_chance` | match_user_stats |
| `criticalStrikeDamage` | `critical_damage` | match_user_stats |
| `coolDownReduction` | `cooldown_reduction` | match_user_stats |
| `lifeSteal` | `life_steal` | match_user_stats |
| `normalLifeSteal` | `normal_life_steal` | match_user_stats |
| `skillLifeSteal` | `skill_life_steal` | match_user_stats |
| `mmrBefore` | `mmr_before` | match_user_mmr |
| `mmrAfter` | `mmr_after` | match_user_mmr |
| `mmrGain` | `mmr_gain` | match_user_mmr |
| `mmrGainInGame` | `mmr_gain_in_game` | match_user_mmr |
| `mmrLossEntryCost` | `mmr_loss_entry_cost` | match_user_mmr |
| `rankPoint` | `rank_point` | match_user_mmr |
| `viewContribution` | `sight_score` | match_user_sight |
| `addTelephotoCamera` | `camera_setup` | match_user_sight |
| `removeTelephotoCamera` | `camera_remove` | match_user_sight |
| `useReconDrone` | `basic_drone_setup` | match_user_sight |
| `useEmpDrone` | `emp_drone_setup` | match_user_sight |
| `equipFirstItemForLog` | `first_*` | match_user_equipment |
| `equipment` | `last_*` | match_user_equipment |
| `bestWeapon` | `best_weapon` | match_user_equipment |
| `bestWeaponLevel` | `best_weapon_level` | match_user_equipment |
| `traitFirstCore` | trait_type=`first_core` | match_user_trait |
| `traitFirstSub` | trait_type=`first_sub` | match_user_trait |
| `traitSecondSub` | trait_type=`second_sub` | match_user_trait |
| `creditSource` | 파싱 후 저장 | match_user_credit_acquisitions |
| `totalVFCredits` | `gain_credit` | match_user_credit_time |
| `usedVFCredits` | `used_credit` | match_user_credit_time |
| `useGadget` | 파싱 후 저장 | match_user_gadget |
| `getBuffCubeRed` 등 | metric_type=`get_cube` | match_user_object |

---

## 주요 코드 값 참조

### 몬스터 ID (`killMonsters` 키)

| ID | 몬스터 |
|----|--------|
| 1 | 닭 |
| 2 | 박쥐 |
| 3 | 들개 |
| 4 | 늑대 |
| 5 | 곰 |
| 6 | 멧돼지 |
| 7 | 위클라인 |
| 8 | 알파 |
| 9 | 오메가 |
| 10 | 감마 |
| 12 | 변이 동물 계열 |

### 장비 슬롯 (equipment / `equipFirstItemForLog` 키)

| 키 | 슬롯 |
|----|------|
| 0 | 무기 |
| 1 | 옷 |
| 2 | 머리 |
| 3 | 팔/장식 |
| 4 | 다리 |

### 전술 스킬 코드 (`tacticalSkillGroup`)

| 코드 | L10N 검색 키 |
|------|-------------|
| 30 | Skill/Group/Name/4000000 |
| 40 | Skill/Group/Name/4001000 |
| 50 | Skill/Group/Name/4101000 |
| 60 | Skill/Group/Name/4102000 |
| 70 | Skill/Group/Name/4103000 |
| 80 | Skill/Group/Name/4104000 |
| 90 | Skill/Group/Name/4105000 |
| 110 | Skill/Group/Name/4107000 |
| 120 | Skill/Group/Name/4110000 |
| 130 | Skill/Group/Name/4112000 |
| 140 | Skill/Group/Name/4113000 |
| 150 | Skill/Group/Name/4108000 |

> [!TIP]
> 전술 스킬 이름은 `l10n[검색 키]`로 조회합니다.

### 가젯 스킬 코드 (`useGadget` 키)

| 코드 | L10N 검색 키 |
|------|-------------|
| 8300301 | Skill/Group/Name/8300300 |
| 8300101 | Skill/Group/Name/8300100 |
| 8300201 | Skill/Group/Name/8300200 |
| 8300401 | Skill/Group/Name/8300400 |
| 8300501 | Skill/Group/Name/8300500 |
| 8310201 | Skill/Group/Name/8310200 |

### 리전 서버 (`serverCode`)

| 코드 | 리전 |
|------|------|
| 10 | Asia (한국 — **수집 대상**) |
| 12 | NA |
| 13 | Europe |
| 14 | South America |
| 17 | Asia2 |
| 18 | Asia3 |

### 매칭 모드 (`matchingMode`)

> [!NOTE]
> `matchingMode`는 게임 모드(Cobalt, union 등)와 매칭 타입(Normal, Ranked 등)의 조합으로 파생된 고유 식별자입니다.

| 값 | 모드 |
|----|------|
| 2 | 스쿼드 일반 |
| 3 | 스쿼드 랭크 (**수집 대상**) |
| 4 | 코발트 일반 |
| 9 | 론울프 |

### 팀 모드 (`matchingTeamMode`)

| 값 | 모드 |
|----|------|
| 1 | 론울프 |
| 3 | 스쿼드 |
| 4 | 코발트 프로토콜 |

---

## 버전 이력

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| v2.4 | 2026-03-16 | 실제 데이터(match_56000302_s9.json) + 공식 API 문서(v9.4.0) 기반 전면 업데이트: UID 불변성 오류 수정(닉네임 변경 시 변경됨), MatchingMode(코발트=4/론울프=9) · TeamMode(코발트=4) 수정, traitFirstCore 추가, 카메라 매핑 명확화, 미수집 필드 대폭 확장(COBALT 전용/Deprecated 구분), 전술스킬·가젯·리전서버 코드 표 추가, API↔DB 매핑 표 전면 재작성 |
| v2.3 | 2026-03-09 | Alembic 38cbb6ad2222 기준 전체 컬럼 동기화, 소스 마스터 테이블 2개 추가, 테이블 수 32개로 수정 |
| v2.2 | 2026-01-30 | 실제 API 응답 기반 미수집 필드 및 코드값 참조 추가 |
| v2.1 | 2026-01-30 | Season 9 스키마 반영, user_num 체계 도입 |
| v2.0 | 2025-12-19 | Wide/Long Format 분리, 크레딧 테이블 정규화 |
| v1.0 | 2025-11-01 | 초기 버전 |
