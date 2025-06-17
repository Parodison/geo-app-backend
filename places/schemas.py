from pydantic import BaseModel

class SearchPlaceByTextQueryModel(BaseModel):
    textQuery: str