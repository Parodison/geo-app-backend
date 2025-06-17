import httpx
from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse
from places.schemas import SearchPlaceByTextQueryModel
from conf.settings import env

router = APIRouter()

@router.post("/search-text")
async def search_place_by_text(query: SearchPlaceByTextQueryModel = Body(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{env.google_places_url}v1/places:searchText",
            headers={
                "X-Goog-Api-Key": env.google_maps_api_key,
                "X-Goog-FieldMask": "places.id,places.formattedAddress,places.location,places.displayName,places.containingPlaces,places.plusCode,places.types"
            },
            json={"textQuery": query.textQuery}
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)
    
@router.post("/reverse-geocode-search")
async def reverse_geocode_search(latitude = Query(...), longitude = Query(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{env.google_maps_api_url}maps/api/geocode/json",
            headers={
                "X-Goog-Api-Key": env.google_maps_api_key,
            },
            params={
                "latlng": f"{latitude}, {longitude}",
                "key": env.google_maps_api_key
            }
        )
        return JSONResponse(content=response.json(), status_code=response.status_code)