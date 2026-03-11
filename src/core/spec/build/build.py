from enum import StrEnum

from pydantic import BaseModel, Field

from .angie import AngieConfig

class Distro(StrEnum):
    SUSE = "suse"

class BuildahConfig(BaseModel):
    Path: str = 'buildah'

class BuildSpec(BaseModel):
    ProjectName: str
    BaseImage: str
    Distro: Distro
    Buildah: BuildahConfig = Field(default_factory=BuildahConfig)
    Angie: AngieConfig = Field(default_factory=AngieConfig)