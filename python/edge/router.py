"""
Developed by PowerShield, as an alternative to Edge Computing
"""

"""Geographic routing logic for intelligent edge request distribution.

This module provides geographic routing capabilities to direct requests to
the optimal edge location based on user location, latency, and availability.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
import random


class RoutingStrategy(Enum):
    """Edge routing strategies."""

    GEOGRAPHIC = "geographic"  # Route to nearest geographic region
    LATENCY = "latency"  # Route based on measured latency
    LOAD_BALANCED = "load_balanced"  # Distribute load across regions
    FAILOVER = "failover"  # Primary with failover to backup
    RANDOM = "random"  # Random distribution


@dataclass
class EdgeLocation:
    """Edge location definition."""

    id: str
    region: str
    latitude: float
    longitude: float
    capacity: int = 100
    current_load: int = 0
    available: bool = True
    priority: int = 1  # Lower = higher priority


@dataclass
class RoutingRule:
    """Routing rule definition."""

    condition: Callable[[Dict[str, Any]], bool]
    target_region: str
    priority: int = 1


class GeoRouter:
    """Geographic router for edge request distribution."""

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.GEOGRAPHIC) -> None:
        """Initialize geo router.

        Args:
            strategy: Routing strategy
        """
        self.strategy = strategy
        self._locations: Dict[str, EdgeLocation] = {}
        self._rules: List[RoutingRule] = []
        self._latency_map: Dict[Tuple[str, str], float] = {}  # (origin, target) -> latency

    def register_location(self, location: EdgeLocation) -> None:
        """Register an edge location.

        Args:
            location: Edge location
        """
        self._locations[location.id] = location

    def add_routing_rule(self, rule: RoutingRule) -> None:
        """Add a custom routing rule.

        Args:
            rule: Routing rule
        """
        self._rules.append(rule)
        # Sort rules by priority
        self._rules.sort(key=lambda r: r.priority)

    def route_request(self, request_info: Dict[str, Any]) -> Optional[EdgeLocation]:
        """Route a request to the optimal edge location.

        Args:
            request_info: Request information including origin, headers, etc.

        Returns:
            Selected edge location or None
        """
        # Check custom rules first
        for rule in self._rules:
            if rule.condition(request_info):
                target_id = self._find_location_in_region(rule.target_region)
                if target_id:
                    return self._locations[target_id]

        # Apply strategy-based routing
        if self.strategy == RoutingStrategy.GEOGRAPHIC:
            return self._route_geographic(request_info)
        elif self.strategy == RoutingStrategy.LATENCY:
            return self._route_latency(request_info)
        elif self.strategy == RoutingStrategy.LOAD_BALANCED:
            return self._route_load_balanced(request_info)
        elif self.strategy == RoutingStrategy.FAILOVER:
            return self._route_failover(request_info)
        elif self.strategy == RoutingStrategy.RANDOM:
            return self._route_random(request_info)

        return None

    def _route_geographic(self, request_info: Dict[str, Any]) -> Optional[EdgeLocation]:
        """Route based on geographic proximity.

        Args:
            request_info: Request information

        Returns:
            Nearest edge location
        """
        origin_lat = request_info.get("latitude")
        origin_lon = request_info.get("longitude")

        if origin_lat is None or origin_lon is None:
            # Fallback to region-based routing
            region = request_info.get("region", "us-east")
            location_id = self._find_location_in_region(region)
            return self._locations.get(location_id) if location_id else None

        # Find nearest available location
        min_distance = float("inf")
        nearest_location = None

        for location in self._locations.values():
            if not location.available:
                continue

            distance = self._calculate_distance(
                origin_lat, origin_lon, location.latitude, location.longitude
            )

            if distance < min_distance:
                min_distance = distance
                nearest_location = location

        return nearest_location

    def _route_latency(self, request_info: Dict[str, Any]) -> Optional[EdgeLocation]:
        """Route based on measured latency.

        Args:
            request_info: Request information

        Returns:
            Lowest latency edge location
        """
        origin = request_info.get("origin", "unknown")

        min_latency = float("inf")
        best_location = None

        for location in self._locations.values():
            if not location.available:
                continue

            latency = self._get_latency(origin, location.id)

            if latency < min_latency:
                min_latency = latency
                best_location = location

        return best_location

    def _route_load_balanced(self, request_info: Dict[str, Any]) -> Optional[EdgeLocation]:
        """Route based on current load.

        Args:
            request_info: Request information

        Returns:
            Least loaded edge location
        """
        available_locations = [loc for loc in self._locations.values() if loc.available]

        if not available_locations:
            return None

        # Find location with lowest load percentage
        best_location = min(
            available_locations, key=lambda loc: loc.current_load / max(loc.capacity, 1)
        )

        return best_location

    def _route_failover(self, request_info: Dict[str, Any]) -> Optional[EdgeLocation]:
        """Route with failover support.

        Args:
            request_info: Request information

        Returns:
            Primary or failover edge location
        """
        # Sort locations by priority
        sorted_locations = sorted(
            self._locations.values(), key=lambda loc: (not loc.available, loc.priority)
        )

        # Return first available location
        for location in sorted_locations:
            if location.available:
                return location

        return None

    def _route_random(self, request_info: Dict[str, Any]) -> Optional[EdgeLocation]:
        """Route randomly among available locations.

        Args:
            request_info: Request information

        Returns:
            Random edge location
        """
        available_locations = [loc for loc in self._locations.values() if loc.available]

        if not available_locations:
            return None

        return random.choice(available_locations)

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two geographic coordinates.

        Uses Haversine formula for great-circle distance.

        Args:
            lat1: Origin latitude
            lon1: Origin longitude
            lat2: Destination latitude
            lon2: Destination longitude

        Returns:
            Distance in kilometers
        """
        import math

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in kilometers
        r = 6371

        return c * r

    def _get_latency(self, origin: str, target: str) -> float:
        """Get measured latency between origin and target.

        Args:
            origin: Origin identifier
            target: Target location ID

        Returns:
            Latency in milliseconds
        """
        key = (origin, target)
        if key in self._latency_map:
            return self._latency_map[key]

        # Default latency if not measured
        return 100.0

    def set_latency(self, origin: str, target: str, latency: float) -> None:
        """Set measured latency between origin and target.

        Args:
            origin: Origin identifier
            target: Target location ID
            latency: Latency in milliseconds
        """
        self._latency_map[(origin, target)] = latency

    def _find_location_in_region(self, region: str) -> Optional[str]:
        """Find an available location in a region.

        Args:
            region: Region identifier

        Returns:
            Location ID or None
        """
        for location in self._locations.values():
            if location.region == region and location.available:
                return location.id

        return None

    def update_load(self, location_id: str, load: int) -> None:
        """Update current load for a location.

        Args:
            location_id: Location ID
            load: Current load
        """
        if location_id in self._locations:
            self._locations[location_id].current_load = load

    def set_availability(self, location_id: str, available: bool) -> None:
        """Set availability status for a location.

        Args:
            location_id: Location ID
            available: Availability status
        """
        if location_id in self._locations:
            self._locations[location_id].available = available

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics.

        Returns:
            Routing statistics
        """
        total_locations = len(self._locations)
        available_locations = sum(1 for loc in self._locations.values() if loc.available)
        total_capacity = sum(loc.capacity for loc in self._locations.values())
        total_load = sum(loc.current_load for loc in self._locations.values())

        return {
            "strategy": self.strategy.value,
            "total_locations": total_locations,
            "available_locations": available_locations,
            "total_capacity": total_capacity,
            "current_load": total_load,
            "load_percentage": (total_load / max(total_capacity, 1)) * 100,
            "regions": list(set(loc.region for loc in self._locations.values())),
        }

    def get_location(self, location_id: str) -> Optional[EdgeLocation]:
        """Get location by ID.

        Args:
            location_id: Location ID

        Returns:
            Edge location or None
        """
        return self._locations.get(location_id)

    def get_locations_by_region(self, region: str) -> List[EdgeLocation]:
        """Get all locations in a region.

        Args:
            region: Region identifier

        Returns:
            List of edge locations
        """
        return [loc for loc in self._locations.values() if loc.region == region]
