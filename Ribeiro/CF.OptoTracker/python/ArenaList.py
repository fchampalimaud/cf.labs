from pydantic import BaseModel, Field
from typing import List, Optional
from _utils import (
    export_schema,
    bonsai_sgen,
    BonsaiSgenSerializers,
    pascal_to_snake_case,
)
from pathlib import Path

class Point(BaseModel):
    x: int = Field(
        default=0, ge=0, description="X coordinate"
    )
    y: int = Field(
        default=0, ge=0, description="Y coordinate"
    )
    

class Arena(BaseModel):
    id: int = Field(
        default=0, ge=0, description="Arena ID"
    )
    
    region: List[Point] = Field( description="List of points that define the arena")
    rois: Optional[List[List[Point]]] = Field(  default=None, description="List of ROI points")

class ArenaList(BaseModel):
    arenas: List[Arena] = Field(description="List of arenas")


if __name__ == "__main__":
    json_schema = export_schema(ArenaList)
    schema_name = ArenaList.__name__
    _dashed = pascal_to_snake_case(schema_name).replace("_", "-")
    schema_path = Path(rf"json/{_dashed}-schema.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write(json_schema)

    bonsai_sgen(
        schema_path=schema_path,
        output_path=Path(rf"bonsai/Extensions/{schema_name}.cs"),
        namespace=schema_name,
        serializer=[BonsaiSgenSerializers.JSON, BonsaiSgenSerializers.YAML],
    )

    arena_example = ArenaList(
        arenas = [
            Arena(
                id = 0,
                region=[
                    Point(x=0, y=0),
                    Point(x=0, y=0),
                    Point(x=0, y=0),
                    Point(x=0, y=0),
                ],                
            ),
            Arena(
                id = 1,
                region=[
                    Point(x=1, y=2),
                    Point(x=1, y=3),
                    Point(x=1, y=2),
                    Point(x=1, y=3),
                ],
            ),
        ],
    )

    with open(
        rf"json/{_dashed}-example.json",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(arena_example.model_dump_json(indent=2))
