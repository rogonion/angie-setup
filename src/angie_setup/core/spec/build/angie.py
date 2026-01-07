from typing import List

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    Dependencies: List[str] = Field(default_factory=list)
    Resources: str = "resources"
    Uid: int = 1002
    Gid: int = 1002


class BuildConfig(BaseModel):
    Dependencies: List[str] = Field(default_factory=list)
    Flags: List[str] = Field(default_factory=list)


class AngieConfig(BaseModel):
    Version: str
    SourceUrl: str
    Prefix: str = '/usr/local/angie'
    Build: BuildConfig = Field(default_factory=BuildConfig)
    Runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)