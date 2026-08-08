from pydantic import BaseModel, ConfigDict


class SupabaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    def to_dict(
        self,
        *,
        exclude_none: bool = False,
        exclude_unset: bool = False,
    ) -> dict:
        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )
