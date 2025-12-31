import os
import json
import abc
from pathlib import Path
from typing import Any, Dict, List
import boto3
from scripts.logger import logger

class DataStorage(abc.ABC):
    """데이터 저장소 추상 기본 클래스"""
    
    @abc.abstractmethod
    def save(self, data: Any, path: str) -> bool:
        """데이터를 저장합니다.
        
        Args:
            data: 저장할 데이터 (JSON 직렬화 가능해야 함)
            path: 저장할 경로 (S3 Key 또는 로컬 파일 경로)
        """
        pass

class LocalStorage(DataStorage):
    """로컬 파일 시스템 저장소"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        
    def save(self, data: Any, path: str) -> bool:
        try:
            full_path = self.root_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            
            logger.info(f"[LocalStorage] Saved data to {full_path}")
            return True
        except Exception as e:
            logger.error(f"[LocalStorage] Failed to save data: {e}")
            return False

class S3Storage(DataStorage):
    """AWS S3 저장소"""
    
    def __init__(self, bucket_name: str, aws_access_key: str = None, aws_secret_key: str = None, region_name: str = "ap-northeast-2"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name
        )
        
    def save(self, data: Any, path: str) -> bool:
        try:
            # JSON 직렬화
            json_data = json.dumps(data, ensure_ascii=False)
            
            # S3 업로드 (Windows 경로 구분자 역슬래시를 슬래시로 변경)
            s3_key = path.replace("\\", "/")
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"[S3Storage] Uploaded data to s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"[S3Storage] Failed to upload data: {e}")
            return False

def get_storage(env: str = "dev") -> DataStorage:
    """환경 변수에 따라 적절한 Storage 객체를 반환하는 팩토리 함수"""
    if env == "prod":
        bucket_name = os.getenv("AWS_S3_BUCKET")
        if not bucket_name:
            logger.warning("AWS_S3_BUCKET is not set. Falling back to LocalStorage.")
            return LocalStorage()
            
        return S3Storage(
            bucket_name=bucket_name,
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "ap-northeast-2")
        )
    else:
        return LocalStorage()