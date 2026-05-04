from fastapi import APIRouter, Depends, HTTPException
from authx import TokenPayload
from app.core.auth import access_token_header
from app.core.logger import get_logger
from app import schemas

log = get_logger(__name__)

router = APIRouter(prefix="/itinerary", tags=["Itinerary"])

PACE_LIMITS = {
    "relaxed": 6 * 60,
    "balanced": 8 * 60,
    "packed": 10 * 60
}

def resolve_daily_limit_mins(pace: str | None) -> int:
    if pace in PACE_LIMITS:
        return PACE_LIMITS[pace]
    return PACE_LIMITS["balanced"]

def squared_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

def poi_point(poi: schemas.ItineraryPOI) -> tuple[float, float]:
    return (poi.coordinates.lat, poi.coordinates.lng)

def kmeans_cluster(pois: list[schemas.ItineraryPOI], days: int, iterations: int = 12) -> list[list[schemas.ItineraryPOI]]:
    if days <= 0:
        return []
    if not pois:
        return [[] for _ in range(days)]

    k = min(days, len(pois))
    centroids = [poi_point(pois[i]) for i in range(k)]
    clusters: list[list[schemas.ItineraryPOI]] = [[] for _ in range(k)]

    for _ in range(iterations):
        clusters = [[] for _ in range(k)]
        for poi in pois:
            point = poi_point(poi)
            idx = min(range(k), key=lambda i: squared_distance(point, centroids[i]))
            clusters[idx].append(poi)

        new_centroids: list[tuple[float, float]] = []
        for i, cluster in enumerate(clusters):
            if cluster:
                avg_lat = sum(item.coordinates.lat for item in cluster) / len(cluster)
                avg_lng = sum(item.coordinates.lng for item in cluster) / len(cluster)
                new_centroids.append((avg_lat, avg_lng))
            else:
                new_centroids.append(centroids[i])

        if new_centroids == centroids:
            break
        centroids = new_centroids

    while len(clusters) < days:
        clusters.append([])

    return clusters

def enforce_daily_limit(
    days: list[list[schemas.ItineraryPOI]],
    daily_limit_mins: int
) -> tuple[list[list[schemas.ItineraryPOI]], list[schemas.ItineraryPOI]]:
    overflow: list[schemas.ItineraryPOI] = []
    adjusted_days: list[list[schemas.ItineraryPOI]] = []

    for day in days:
        day_items = list(day)
        total_minutes = sum(item.durationMins for item in day_items)

        if total_minutes > daily_limit_mins:
            removal_candidates = sorted(
                day_items,
                key=lambda item: (item.priority, item.durationMins),
                reverse=True
            )
            for item in removal_candidates:
                if total_minutes <= daily_limit_mins:
                    break
                day_items.remove(item)
                overflow.append(item)
                total_minutes -= item.durationMins

        adjusted_days.append(day_items)

    return adjusted_days, overflow

def nearest_neighbor_route(pois: list[schemas.ItineraryPOI]) -> list[schemas.ItineraryPOI]:
    if len(pois) <= 2:
        return pois

    remaining = list(pois[1:])
    route = [pois[0]]
    current = pois[0]

    while remaining:
        current_point = poi_point(current)
        next_index = min(
            range(len(remaining)),
            key=lambda i: squared_distance(current_point, poi_point(remaining[i]))
        )
        next_poi = remaining.pop(next_index)
        route.append(next_poi)
        current = next_poi

    return route

@router.post("/allocate", response_model=schemas.ItineraryAllocateResponse)
async def allocate_itinerary(
    request: schemas.ItineraryAllocateRequest,
    token: TokenPayload = Depends(access_token_header)
):
    if request.days <= 0:
        raise HTTPException(status_code=400, detail="Number of days must be greater than zero.")

    daily_limit = resolve_daily_limit_mins(request.pace)
    log.info("Allocating itinerary for user %s with %s days", token.sub, request.days)

    clusters = kmeans_cluster(request.unscheduled, request.days)
    adjusted_days, overflow = enforce_daily_limit(clusters, daily_limit)

    return schemas.ItineraryAllocateResponse(
        days=adjusted_days,
        unscheduled=overflow,
        daily_limit_mins=daily_limit
    )

@router.post("/route-day", response_model=list[schemas.ItineraryPOI])
async def route_day(
    request: schemas.ItineraryRouteDayRequest,
    token: TokenPayload = Depends(access_token_header)
):
    log.info("Routing day itinerary for user %s with %s stops", token.sub, len(request.pois))

    try:
        return nearest_neighbor_route(request.pois)
    except Exception as exc:
        log.exception("Failed to optimize route: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to optimize route.")
