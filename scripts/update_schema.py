import re
import sqlparse
import argparse
import hashlib
from sqlalchemy import inspect, text, Table, Column, String, DateTime, MetaData
from sqlalchemy.engine import Engine
from collections import defaultdict
from datetime import datetime

from scripts.config import SCHEMA_PATH
from scripts.db_utils import get_engine
from scripts.logger import logger

VERSION_TABLE_NAME = 'schema_versions'

def get_or_create_version_table(engine: Engine):
    """데이터베이스에 버전 관리 테이블이 없으면 생성합니다."""
    inspector = inspect(engine)
    if not inspector.has_table(VERSION_TABLE_NAME):
        logger.info(f"'{VERSION_TABLE_NAME}' table not found. Creating it...")
        meta = MetaData()
        Table(
            VERSION_TABLE_NAME, meta,
            Column('version_hash', String(64), primary_key=True),
            Column('applied_on', DateTime, nullable=False, default=datetime.utcnow)
        )
        with engine.connect() as conn:
            with conn.begin():
                meta.create_all(conn)
        logger.info(f"'{VERSION_TABLE_NAME}' table created successfully.")

def get_current_db_version(engine: Engine) -> str | None:
    """DB에 적용된 최신 스키마 파일의 해시를 반환합니다."""
    get_or_create_version_table(engine)
    with engine.connect() as conn:
        query = text(f"SELECT version_hash FROM {VERSION_TABLE_NAME} ORDER BY applied_on DESC LIMIT 1")
        result = conn.execute(query).scalar_one_or_none()
        return result

def set_db_version(conn, version_hash: str):
    """
    새로운 버전 정보를 DB에 기록합니다.
    이미 존재하는 버전이면 applied_on만 업데이트합니다.
    """
    # 수정: INSERT ... ON DUPLICATE KEY UPDATE 사용
    query = text(f"""
        INSERT INTO {VERSION_TABLE_NAME} (version_hash, applied_on) 
        VALUES (:hash, :date)
        ON DUPLICATE KEY UPDATE applied_on = :date
    """)
    conn.execute(query, {'hash': version_hash, 'date': datetime.utcnow()})

def get_file_hash(file_path: str) -> str:
    """파일 내용의 SHA256 해시를 계산합니다."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except FileNotFoundError:
        return ""
    
def parse_schema_from_file(file_path: str) -> dict:
    """
    .sql 파일을 파싱하여 테이블별 컬럼과 제약 조건(PK, UNIQUE) 정보를 반환합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"Schema file not found: {file_path}")
        return {}

    schema = {}
    statements = sqlparse.parse(content)

    for stmt in statements:
        if not stmt.get_type() == 'CREATE' or 'TABLE' not in str(stmt).upper():
            continue

        table_name_match = re.search(r"CREATE TABLE\s+`?(\w+)`?", str(stmt), re.IGNORECASE)
        if not table_name_match:
            continue
        table_name = table_name_match.group(1).lower()

        schema[table_name] = {'columns': {}, 'constraints': {'primary_key': [], 'unique': []}}
        
        paren = next((t for t in stmt.tokens if isinstance(t, sqlparse.sql.Parenthesis)), None)
        if not paren:
            continue

        inner_content = ''.join(str(t) for t in paren.tokens).strip()[1:-1]
        lines = [line.strip() for line in inner_content.split('\n')]

        for line in lines:
            line_lower = line.lower()
            if line_lower.startswith(('constraint', 'primary key', 'unique key', 'key', 'foreign key', 'index')):
                pk_match = re.search(r'(?:constraint\s+`?\w+`?\s+)?primary key\s*\((.*?)\)', line_lower)
                if pk_match:
                    cols = [c.strip().replace('`', '') for c in pk_match.group(1).split(',')]
                    schema[table_name]['constraints']['primary_key'] = sorted(cols)
                
                uq_match = re.search(r'(?:constraint\s+(`?\w+`?)\s+)?unique key\s*(?:`?\w*`?)?\s*\((.*?)\)', line_lower)
                if uq_match:
                    constraint_name = uq_match.group(1).strip().replace('`', '') if uq_match.group(1) else f"uq_{table_name}_{len(schema[table_name]['constraints']['unique'])}"
                    cols = [c.strip().replace('`', '') for c in uq_match.group(2).split(',')]
                    schema[table_name]['constraints']['unique'].append({'name': constraint_name, 'columns': sorted(cols)})
                continue

            col_match = re.match(r"`?(\w+)`?\s+(.*)", line)
            if col_match:
                col_name = col_match.group(1).lower()
                col_definition = col_match.group(2).rstrip(',').strip()
                
                if 'primary key' in col_definition.lower():
                    schema[table_name]['constraints']['primary_key'] = [col_name]
                    col_definition = re.sub(r'\s+primary\s+key', '', col_definition, flags=re.IGNORECASE).strip()
                
                if re.search(r'\bunique\b', col_definition.lower()):
                    constraint_name = f"uq_{table_name}_{col_name}"
                    schema[table_name]['constraints']['unique'].append({'name': constraint_name, 'columns': [col_name]})
                    col_definition = re.sub(r'\s+unique', '', col_definition, flags=re.IGNORECASE).strip()
                
                schema[table_name]['columns'][col_name] = col_definition

        for pk_col in schema[table_name]['constraints']['primary_key']:
            if pk_col in schema[table_name]['columns'] and 'not null' not in schema[table_name]['columns'][pk_col].lower():
                 schema[table_name]['columns'][pk_col] += ' NOT NULL'
    
    return schema


def get_current_db_schema(inspector) -> dict:
    """현재 DB의 스키마 정보를 SQLAlchemy Inspector를 통해 가져옵니다."""
    db_schema = {}
    for table_name in inspector.get_table_names():
        if table_name == VERSION_TABLE_NAME:
            continue
        
        table_name_lower = table_name.lower()
        pk_constraint = inspector.get_pk_constraint(table_name)
        
        db_schema[table_name_lower] = {'columns': {}, 'constraints': {
            'primary_key': sorted(pk_constraint['constrained_columns']),
            'unique': []
        }}
        
        unique_constraints = inspector.get_unique_constraints(table_name)
        for const in unique_constraints:
            db_schema[table_name_lower]['constraints']['unique'].append({
                'name': const['name'],
                'columns': sorted(const['column_names'])
            })

        for col in inspector.get_columns(table_name):
            col_name_lower = col['name'].lower()
            col_type = col['type'].compile(dialect=inspector.engine.dialect)
            definition = col_type
            if not col['nullable']:
                definition += " NOT NULL"
            if col['default'] is not None:
                default_val = col['default']
                if isinstance(default_val, str):
                    definition += f" DEFAULT '{default_val}'"
                else:
                    definition += f" DEFAULT {default_val}"
            
            comment = col.get('comment')
            if comment:
                definition += f" COMMENT '{comment}'"
            db_schema[table_name_lower]['columns'][col_name_lower] = definition
            
    return db_schema
def normalize_definition(defn_str: str) -> str:
    """비교를 위해 컬럼 정의 문자열을 정규화합니다. COMMENT는 비교에서 제외합니다."""
    s = defn_str.lower()
    s = re.sub(r"\s+comment\s+'.*?'", '', s).strip()
    s = re.sub(r"\s+collate\s+[\w_]+", '', s).strip()
    s = s.replace('integer', 'int').replace('boolean', 'tinyint(1)')
    s = s.replace("'current_timestamp'", "current_timestamp")
    
    parts = s.split()
    dtype_match = re.match(r"(\w+\(\d+(,\s*\d+)?\))", s)
    dtype = None
    if dtype_match:
        dtype = dtype_match.group(1)
        temp_parts = [p for p in parts if not p.startswith(dtype)]
        parts = temp_parts
    
    default_part = ""
    if 'default' in parts:
        idx = parts.index('default')
        default_part = ' '.join(parts[idx:])
        parts = parts[:idx]

    parts.sort()
    
    if dtype:
        parts.insert(0, dtype)

    normalized = ' '.join(parts)
    if default_part:
        normalized += f" {default_part}"

    return normalized.strip()



# ============================================================
# 수정: 컬럼 삭제 탐지 추가
# ============================================================
def compare_and_plan_changes(target_schema, db_schema, allow_deletes=False):
    """
    두 스키마를 비교하여 변경 계획을 생성합니다.
    
    Args:
        target_schema: 목표 스키마 (schema_season9.sql)
        db_schema: 현재 DB 스키마
        allow_deletes: True면 DROP COLUMN/TABLE 포함, False면 경고만
    """
    plan = defaultdict(list)
    warnings = []
    
    target_tables = set(target_schema.keys())
    db_tables = set(db_schema.keys())

    # 1. 신규 테이블 (아직 자동 생성 미지원)
    for table_name in target_tables - db_tables:
        warnings.append(f"⚠️  Table '{table_name}' exists in schema file but not in DB.")

    # 2. 삭제된 테이블
    for table_name in db_tables - target_tables:
        if allow_deletes:
            plan['drop_tables'].append({
                'table_name': table_name,
                'sql': f"DROP TABLE `{table_name}`;"
            })
        else:
            warnings.append(f"⚠️  Table '{table_name}' exists in DB but not in schema file. Use --allow-deletes to drop.")

    # 3. 기존 테이블의 컬럼 비교
    for table_name in target_tables.intersection(db_tables):
        target_cols = target_schema[table_name]['columns']
        db_cols = db_schema[table_name]['columns']
        
        # 3-1. 신규 컬럼
        for col_name, definition in target_cols.items():
            if col_name not in db_cols:
                plan['add_columns'].append({
                    'table_name': table_name, 
                    'column_name': col_name, 
                    'definition': definition, 
                    'sql': f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {definition};"
                })
        
        # 3-2. 삭제된 컬럼 (새로 추가!)
        for col_name, db_def in db_cols.items():
            if col_name not in target_cols:
                if allow_deletes:
                    plan['drop_columns'].append({
                        'table_name': table_name,
                        'column_name': col_name,
                        'old_definition': db_def,
                        'sql': f"ALTER TABLE `{table_name}` DROP COLUMN `{col_name}`;"
                    })
                else:
                    warnings.append(
                        f"⚠️  Column '{table_name}.{col_name}' exists in DB but not in schema file.\n"
                        f"    Current definition: {db_def}\n"
                        f"    Use --allow-deletes to drop (DATA WILL BE LOST!)."
                    )
        
        # 3-3. 수정된 컬럼
        for col_name in target_cols.keys() & db_cols.keys():
            target_def = target_cols[col_name]
            db_def = db_cols[col_name]
            
            if normalize_definition(db_def) != normalize_definition(target_def):
                plan['modify_columns'].append({
                    'table_name': table_name, 
                    'column_name': col_name, 
                    'from': db_def, 
                    'to': target_def, 
                    'sql': f"ALTER TABLE `{table_name}` MODIFY COLUMN `{col_name}` {target_def};"
                })
        
        # 4. 제약조건 비교 (UNIQUE)
        target_constraints_uq = {tuple(c['columns']): c['name'] for c in target_schema[table_name]['constraints']['unique']}
        db_constraints_uq = {tuple(c['columns']): c['name'] for c in db_schema[table_name]['constraints']['unique']}

        for columns, name in target_constraints_uq.items():
            if columns not in db_constraints_uq:
                cols_str = ', '.join([f"`{c}`" for c in columns])
                plan['add_constraints'].append({
                    'table_name': table_name, 
                    'sql': f"ALTER TABLE `{table_name}` ADD CONSTRAINT `{name}` UNIQUE ({cols_str});"
                })
        
        # 삭제된 제약조건
        for columns, name in db_constraints_uq.items():
            if columns not in target_constraints_uq:
                if allow_deletes:
                    plan['drop_constraints'].append({
                        'table_name': table_name,
                        'constraint_name': name,
                        'sql': f"ALTER TABLE `{table_name}` DROP INDEX `{name}`;"
                    })
                else:
                    warnings.append(f"⚠️  UNIQUE constraint '{name}' on '{table_name}' will be dropped with --allow-deletes.")
    
    return plan, warnings


# ============================================================
# 수정: 삭제 작업 포함
# ============================================================
def run_migration(engine: Engine, plan: dict, version_hash: str, allow_deletes=False):
    """
    생성된 계획에 따라 안전 검사를 수행하고 마이그레이션을 실행합니다.
    """
    # 삭제 작업 순서: 제약조건 → 컬럼 → 테이블
    all_sql = []
    
    if allow_deletes:
        all_sql.extend([item['sql'] for item in plan.get('drop_constraints', [])])
    
    all_sql.extend([item['sql'] for item in plan.get('add_columns', [])])
    all_sql.extend([item['sql'] for item in plan.get('modify_columns', [])])
    
    if allow_deletes:
        all_sql.extend([item['sql'] for item in plan.get('drop_columns', [])])
    
    all_sql.extend([item['sql'] for item in plan.get('add_constraints', [])])
    
    if allow_deletes:
        all_sql.extend([item['sql'] for item in plan.get('drop_tables', [])])

    if not all_sql:
        logger.info("No executable changes in the plan.")
        # 수정: 변경사항 없어도 버전 업데이트 (ON DUPLICATE KEY UPDATE로 안전)
        with engine.connect() as conn:
            with conn.begin():
                set_db_version(conn, version_hash)
        return

    try:
        with engine.begin() as conn:
            logger.info("Starting migration within a transaction...")
            
            # 사전 검사
            logger.info("Running pre-migration safety checks...")
            for item in plan.get('modify_columns', []):
                if not pre_migration_safety_check(conn, item['table_name'], item['column_name'], item['to']):
                    raise Exception(f"Safety check failed for column '{item['column_name']}' in table '{item['table_name']}'. Aborting migration.")
            
            if allow_deletes:
                drop_count = len(plan.get('drop_columns', [])) + len(plan.get('drop_tables', []))
                if drop_count > 0:
                    logger.warning(f"DANGER: {drop_count} DROP operations will be executed. DATA WILL BE LOST!")
            
            logger.info("All safety checks passed.")
            
            # 마이그레이션 실행 (중첩된 with conn.begin() 제거)
            for sql in all_sql:
                logger.info(f"Executing: {sql.strip()}")
                conn.execute(text(sql))
            
            # 버전 업데이트
            set_db_version(conn, version_hash)
            logger.info("Updating version table...")
            
            # 컨텍스트 매니저 종료 시 자동 커밋됨
            logger.info("Schema migration applied successfully! Transaction has been committed.")

    except Exception as e:
        # 예외 발생 시 자동 롤백됨
        logger.error(f"An error occurred during migration: {e}")
        logger.error("Migration failed. The transaction has been rolled back.")
        raise


def pre_migration_safety_check(conn, table: str, column: str, new_definition: str) -> bool:
    """데이터 손실 가능성이 있는 스키마 변경을 사전에 검사합니다."""
    # 1. VARCHAR 길이 축소
    varchar_match = re.search(r'varchar\((\d+)\)', new_definition, re.IGNORECASE)
    if varchar_match:
        new_len = int(varchar_match.group(1))
        query = text(f"SELECT 1 FROM `{table}` WHERE CHAR_LENGTH(`{column}`) > :new_len LIMIT 1")
        if conn.execute(query, {'new_len': new_len}).scalar_one_or_none():
            logger.error(f"SAFETY CHECK FAILED: Data in `{table}`.`{column}` would be truncated.")
            return False

    # 2. NOT NULL 추가
    if 'not null' in new_definition.lower():
        query = text(f"SELECT 1 FROM `{table}` WHERE `{column}` IS NULL LIMIT 1")
        if conn.execute(query).scalar_one_or_none():
            logger.error(f"SAFETY CHECK FAILED: Cannot add NOT NULL to `{table}`.`{column}` (contains NULL).")
            return False

    return True


# ============================================================
# 수정: 리포트 개선 및 --allow-deletes 플래그 추가
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Database Schema Migration Tool.")
    parser.add_argument('--apply', action='store_true', help="Apply the planned database changes.")
    parser.add_argument('--allow-deletes', action='store_true', 
                       help="Allow DROP TABLE/COLUMN operations (⚠️  DATA LOSS!).")
    parser.add_argument('--debug', action='store_true', help="Enable detailed debug output.")
    # 추가: --force 플래그
    parser.add_argument('--force', action='store_true', 
                       help="Force execution even if DB version matches file version.")
    args = parser.parse_args()

    engine = get_engine()
    logger.info("Starting database schema update...")

    # 버전 확인
    file_hash = get_file_hash(SCHEMA_PATH)
    db_hash = get_current_db_version(engine)

    logger.info(f"Current DB version: {db_hash[:8] if db_hash else 'None'}")
    logger.info(f"Target file version: {file_hash[:8]}")

    # 수정: 버전이 같아도 구조 변경이 있으면 계속 진행
    # (이전에는 early return으로 종료했음)
    
    # 스키마 분석
    logger.info(f"Loading target schema from '{SCHEMA_PATH}'...")
    target_schema = parse_schema_from_file(SCHEMA_PATH)
    
    if not target_schema:
        logger.error("Could not load target schema. Aborting.")
        return

    logger.info("Loading current database schema...")
    inspector = inspect(engine)
    db_schema = get_current_db_schema(inspector)

    logger.info("Comparing schemas and planning changes...")
    plan, warnings = compare_and_plan_changes(target_schema, db_schema, args.allow_deletes)

    # 경고 출력
    if warnings:
        print("\n⚠️  === WARNINGS ===")
        for warning in warnings:
            print(warning)
        print("=" * 70 + "\n")

    # 리포트 생성
    report = defaultdict(list)
    
    for item in plan.get('add_columns', []):
        report[item['table_name']].append(f"  ADD Column '{item['column_name']}': {item['definition']}")
    
    for item in plan.get('modify_columns', []):
        report[item['table_name']].append(
            f"  ~ MODIFY Column '{item['column_name']}':\n"
            f"      FROM: {item['from']}\n"
            f"      TO:   {item['to']}"
        )
    
    for item in plan.get('drop_columns', []):
        report[item['table_name']].append(
            f"  ✗ DROP Column '{item['column_name']}' (was: {item['old_definition']}) [DATA LOSS!]"
        )
    
    for item in plan.get('drop_tables', []):
        report[item['table_name']].append(f"  ✗ DROP TABLE '{item['table_name']}' [ENTIRE TABLE LOST!]")
    
    for item in plan.get('add_constraints', []):
        report[item['table_name']].append(f"  + ADD UNIQUE constraint")
    
    for item in plan.get('drop_constraints', []):
        report[item['table_name']].append(f"  - DROP constraint '{item['constraint_name']}'")

    if not report:
        # 변경사항 없고 버전도 같으면 종료
        if file_hash == db_hash:
            logger.info("Database schema is already up to date.")
            return
        
        logger.info("No structural schema changes detected.")
        logger.info("Updating version info only.")
        if args.apply:
            with engine.connect() as conn:
                with conn.begin():
                    set_db_version(conn, file_hash)
            logger.info("Version information updated successfully.")
        return

    # 변경 계획 출력
    print("\n" + "=" * 70)
    print("MIGRATION PLAN")
    print("=" * 70)
    for table_name, changes in sorted(report.items()):
        print(f"\nTable: {table_name}")
        for change in changes:
            print(change)
    print("\n" + "=" * 70 + "\n")

    # 실행
    if args.apply:
        if plan.get('drop_columns') or plan.get('drop_tables'):
            print("🚨 WARNING: This migration includes DROP operations!")
            print("🚨 DATA WILL BE PERMANENTLY DELETED!")
        
        print("\nAre you sure you want to apply these changes?")
        choice = input("Type 'yes' to continue: ")
        
        if choice.lower() == 'yes':
            run_migration(engine, plan, file_hash, args.allow_deletes)
        else:
            logger.info("Migration cancelled by user.")
    else:
        logger.info("This was a dry run. Use --apply to execute.")


if __name__ == "__main__":
    main()