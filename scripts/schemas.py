from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    uid: str = Field(alias="userId")
    nickname: str

class UserGame(BaseModel):
    model_config = ConfigDict(extra='allow') # Allow extra fields for flexibility

    gameId: int
    seasonId: int
    matchingMode: int
    matchingTeamMode: int
    characterNum: int
    teamNumber: int
    gameRank: int
    playerKill: int = 0
    playerAssistant: int = 0
    playerDeaths: int = 0
    monsterKill: int = 0
    totalTime: int
    startDtm: str
    versionMajor: int
    versionMinor: int
    versionSeason: int = 0
    serverName: str
    mmrAvg: int = 0
    # uid will be populated during batch processing if not present
    uid: Optional[str] = None 

class MatchResponse(BaseModel):
    code: int
    message: str
    userGames: List[UserGame] # Strict validation for core fields, flexible for others

class TopRankerResponse(BaseModel):
    code: int
    topRanks: List[Dict[str, Any]]
