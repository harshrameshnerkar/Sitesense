"""
Zone and Counting Line Configuration Route for SiteSense.
Stores and serves spatial polygon boundaries and directional tripwires per site.
"""

from typing import Optional
from fastapi import APIRouter, Query
from services.core.schemas import ZoneConfigResponse, ZoneSaveRequest

router = APIRouter(prefix="/zones", tags=["Zones"])

# In-memory / config storage for zone polygons
_MOCK_ZONES = {
    7: {
        "zones": [
            {
                "id": "walkway_a",
                "name": "Primary Pedestrian Thoroughfare A",
                "polygon": [[100, 200], [800, 200], [800, 450], [100, 450]],
                "type": "clearance_mandatory"
            },
            {
                "id": "loading_bay_4",
                "name": "Loading Bay Intake Area",
                "polygon": [[200, 50], [600, 50], [600, 300], [200, 300]],
                "type": "ppe_helmet_required"
            }
        ],
        "lines": [
            {
                "id": "inbound_count_line",
                "name": "Forklift Intake Line",
                "coordinates": [[300, 400], [700, 400]],
                "direction": "down"
            }
        ]
    }
}


@router.get("", response_model=ZoneConfigResponse)
def get_zones(site_id: int = Query(7, description="Site ID")):
    """
    Retrieve polygon zones and counting line definitions for a site.
    """
    config = _MOCK_ZONES.get(site_id, {"zones": [], "lines": []})
    return ZoneConfigResponse(zones=config["zones"], lines=config["lines"])


@router.post("")
def save_zones(payload: ZoneSaveRequest):
    """
    Save polygon zones and counting line configurations without code changes.
    """
    _MOCK_ZONES[payload.site_id] = {
        "zones": payload.zones,
        "lines": payload.lines
    }
    return {"saved": True, "site_id": payload.site_id}

