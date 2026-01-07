from pydantic import BaseModel, Field

from .angie import AngieConfig


class BuildahConfig(BaseModel):
    Path: str = 'buildah'

class BuildSpec(BaseModel):
    ProjectName: str
    BaseImage: str
    Buildah: BuildahConfig = Field(default_factory=BuildahConfig)
    Angie: AngieConfig = Field(default_factory=AngieConfig)