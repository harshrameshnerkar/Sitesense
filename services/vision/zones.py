"""
Zone and Region Engine for SiteSense.
Uses Shapely for 2D spatial polygon geometry and evaluates whether detected objects
fall inside designated walkways, danger zones, or loading bays.
"""

from typing import List, Dict, Any, Optional
from shapely.geometry import Polygon, Point, box


class ZoneEngine:
    """
    Evaluates spatial relationship between object bounding boxes and site polygon zones.
    """

    def __init__(self, zone_configs: Optional[List[Dict[str, Any]]] = None):
        self.zones: List[Dict[str, Any]] = []
        if zone_configs:
            for z in zone_configs:
                self.add_zone(z["id"], z["name"], z["polygon"], z.get("type", "general"))

    def add_zone(self, zone_id: str, name: str, polygon_coords: List[List[float]], zone_type: str = "general"):
        """Register a polygon zone."""
        poly = Polygon(polygon_coords)
        self.zones.append({
            "id": zone_id,
            "name": name,
            "polygon": poly,
            "type": zone_type,
            "raw_coords": polygon_coords
        })

    def evaluate_zone(self, bbox: List[int]) -> Optional[str]:
        """
        Given a bounding box [x1, y1, x2, y2], determine which zone it occupies.
        Uses bottom-center contact point (ground anchor) and bounding box overlap.
        """
        x1, y1, x2, y2 = bbox
        bottom_center = Point((x1 + x2) / 2.0, float(y2))
        centroid = Point((x1 + x2) / 2.0, (y1 + y2) / 2.0)
        bbox_poly = box(x1, y1, x2, y2)

        # 1. Check if ground contact point is inside any polygon
        for z in self.zones:
            poly: Polygon = z["polygon"]
            if poly.contains(bottom_center) or poly.contains(centroid):
                return z["id"]

        # 2. Check if bbox intersects significantly (>30% area overlap)
        for z in self.zones:
            poly: Polygon = z["polygon"]
            if poly.intersects(bbox_poly):
                intersection_area = poly.intersection(bbox_poly).area
                bbox_area = max(1.0, (x2 - x1) * (y2 - y1))
                if intersection_area / bbox_area > 0.25:
                    return z["id"]

        return None

