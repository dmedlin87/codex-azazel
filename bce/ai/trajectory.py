"""
Narrative Trajectory Mapping for Codex Azazel.

Tracks how narratives evolve across sources with geospatial and temporal data.
Visualizes divergent narrative paths (e.g., Mark's single Jerusalem visit vs.
John's multiple visits).

Key features:
- Geographic coordinates for events
- Per-source narrative sequences
- Divergent trajectory visualization data
- Temporal progression tracking
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .. import queries, storage


@dataclass
class GeoLocation:
    """Geographic location with coordinates and metadata."""

    name: str  # e.g., "Jerusalem", "Galilee", "Capernaum"
    latitude: float
    longitude: float
    region: Optional[str] = None  # e.g., "Judea", "Galilee", "Samaria"
    modern_name: Optional[str] = None


# Biblical location database with coordinates
BIBLICAL_LOCATIONS: Dict[str, GeoLocation] = {
    "jerusalem": GeoLocation("Jerusalem", 31.7683, 35.2137, "Judea", "Jerusalem"),
    "bethlehem": GeoLocation("Bethlehem", 31.7054, 35.2024, "Judea", "Bethlehem"),
    "nazareth": GeoLocation("Nazareth", 32.6996, 35.3035, "Galilee", "Nazareth"),
    "capernaum": GeoLocation("Capernaum", 32.8803, 35.5753, "Galilee", "Kfar Nahum"),
    "bethsaida": GeoLocation("Bethsaida", 32.9083, 35.6306, "Galilee", "Et-Tell"),
    "cana": GeoLocation("Cana", 32.7469, 35.3394, "Galilee", "Kafr Kanna"),
    "tiberias": GeoLocation("Tiberias", 32.7922, 35.5322, "Galilee", "Tiberias"),
    "sea_of_galilee": GeoLocation("Sea of Galilee", 32.8300, 35.5900, "Galilee", "Lake Kinneret"),
    "jordan_river": GeoLocation("Jordan River", 32.7000, 35.5700, "Jordan Valley", "Jordan River"),
    "jericho": GeoLocation("Jericho", 31.8667, 35.4500, "Judea", "Jericho"),
    "bethany": GeoLocation("Bethany", 31.7700, 35.2600, "Judea", "Al-Eizariya"),
    "samaria": GeoLocation("Samaria", 32.2750, 35.1900, "Samaria", "Sebastia"),
    "sychar": GeoLocation("Sychar", 32.2133, 35.2850, "Samaria", "Askar"),
    "caesarea_philippi": GeoLocation("Caesarea Philippi", 33.2486, 35.6939, "Northern Israel", "Banias"),
    "mount_tabor": GeoLocation("Mount Tabor", 32.6869, 35.3917, "Galilee", "Har Tavor"),
    "mount_of_olives": GeoLocation("Mount of Olives", 31.7784, 35.2453, "Judea", "Mount of Olives"),
    "golgotha": GeoLocation("Golgotha", 31.7785, 35.2296, "Jerusalem", "Church of Holy Sepulchre"),
    "emmaus": GeoLocation("Emmaus", 31.8389, 34.9889, "Judea", "Emmaus Nicopolis"),
    "damascus": GeoLocation("Damascus", 33.5138, 36.2765, "Syria", "Damascus"),
    "antioch": GeoLocation("Antioch", 36.2000, 36.1500, "Syria", "Antakya"),
    "ephesus": GeoLocation("Ephesus", 37.9411, 27.3419, "Asia Minor", "Selcuk"),
    "corinth": GeoLocation("Corinth", 37.9060, 22.8780, "Greece", "Korinthos"),
    "rome": GeoLocation("Rome", 41.9028, 12.4964, "Italy", "Rome"),
    "egypt": GeoLocation("Egypt", 26.8206, 30.8025, "Egypt", "Egypt"),
}


@dataclass
class NarrativeWaypoint:
    """A point in a character's narrative journey."""

    sequence: int  # Order in the narrative
    location_id: str  # Key in BIBLICAL_LOCATIONS
    event_id: Optional[str] = None  # Related BCE event
    reference: Optional[str] = None  # Scripture reference
    description: Optional[str] = None


@dataclass
class SourceTrajectory:
    """A character's narrative trajectory in a specific source."""

    character_id: str
    source_id: str
    waypoints: List[NarrativeWaypoint] = field(default_factory=list)
    total_distance_km: float = 0.0
    unique_locations: int = 0


@dataclass
class TrajectoryComparison:
    """Comparison of trajectories across sources."""

    character_id: str
    sources: List[str]
    divergence_points: List[Dict[str, Any]]
    convergence_points: List[Dict[str, Any]]
    total_divergence_score: float


def get_location(location_id: str) -> Optional[GeoLocation]:
    """Get a biblical location by ID."""
    return BIBLICAL_LOCATIONS.get(location_id.lower().replace(" ", "_"))


def list_locations() -> List[Dict[str, Any]]:
    """List all available biblical locations."""
    return [
        {
            "id": loc_id,
            "name": loc.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "region": loc.region,
        }
        for loc_id, loc in BIBLICAL_LOCATIONS.items()
    ]


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Calculate distance in km between two coordinates using Haversine formula."""
    import math

    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) *
        math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def _extract_location_from_reference(reference: str) -> Optional[str]:
    """Attempt to extract location from a scripture reference or event."""
    ref_lower = reference.lower()

    # Map common reference patterns to locations
    location_hints = {
        "jerusalem": "jerusalem",
        "temple": "jerusalem",
        "golgotha": "golgotha",
        "calvary": "golgotha",
        "galilee": "sea_of_galilee",
        "capernaum": "capernaum",
        "nazareth": "nazareth",
        "bethlehem": "bethlehem",
        "bethany": "bethany",
        "jordan": "jordan_river",
        "samaria": "samaria",
        "sychar": "sychar",
        "cana": "cana",
        "damascus": "damascus",
        "mount of olives": "mount_of_olives",
        "gethsemane": "mount_of_olives",
        "emmaus": "emmaus",
    }

    for hint, loc_id in location_hints.items():
        if hint in ref_lower:
            return loc_id

    return None


def build_character_trajectory(
    char_id: str,
    source_id: str,
) -> SourceTrajectory:
    """Build a narrative trajectory for a character in a specific source.

    Parameters
    ----------
    char_id : str
        Character ID
    source_id : str
        Source to analyze

    Returns
    -------
    SourceTrajectory
        The character's journey through locations in this source
    """
    char = queries.get_character(char_id)
    profile = char.get_source_profile(source_id)

    if profile is None:
        return SourceTrajectory(
            character_id=char_id,
            source_id=source_id,
            waypoints=[],
            total_distance_km=0.0,
            unique_locations=0,
        )

    # Extract locations from references
    waypoints: List[NarrativeWaypoint] = []
    seen_locations: set = set()

    for i, ref in enumerate(profile.references):
        loc_id = _extract_location_from_reference(ref)
        if loc_id:
            seen_locations.add(loc_id)
            waypoints.append(NarrativeWaypoint(
                sequence=i + 1,
                location_id=loc_id,
                reference=ref,
            ))

    # Calculate total distance
    total_dist = 0.0
    for i in range(1, len(waypoints)):
        loc1 = get_location(waypoints[i - 1].location_id)
        loc2 = get_location(waypoints[i].location_id)
        if loc1 and loc2:
            total_dist += haversine_distance(
                loc1.latitude, loc1.longitude,
                loc2.latitude, loc2.longitude
            )

    return SourceTrajectory(
        character_id=char_id,
        source_id=source_id,
        waypoints=waypoints,
        total_distance_km=round(total_dist, 2),
        unique_locations=len(seen_locations),
    )


def build_event_trajectory(event_id: str) -> Dict[str, Any]:
    """Build trajectory data for an event across sources.

    Shows how different sources locate and sequence the event.

    Parameters
    ----------
    event_id : str
        Event ID

    Returns
    -------
    dict
        Trajectory data with locations per source
    """
    event = queries.get_event(event_id)

    source_locations: Dict[str, Dict[str, Any]] = {}

    for account in event.accounts:
        loc_id = _extract_location_from_reference(account.reference)
        if loc_id:
            loc = get_location(loc_id)
            source_locations[account.source_id] = {
                "location_id": loc_id,
                "location_name": loc.name if loc else loc_id,
                "coordinates": [loc.latitude, loc.longitude] if loc else None,
                "reference": account.reference,
            }

    return {
        "event_id": event_id,
        "label": event.label,
        "source_locations": source_locations,
        "location_consensus": len(set(
            v["location_id"] for v in source_locations.values()
        )) == 1,
    }


def compare_trajectories(
    char_id: str,
    source_ids: List[str],
) -> TrajectoryComparison:
    """Compare a character's trajectory across multiple sources.

    Identifies where sources diverge and converge in their
    geographic portrayal of the character.

    Parameters
    ----------
    char_id : str
        Character ID
    source_ids : list of str
        Sources to compare

    Returns
    -------
    TrajectoryComparison
        Detailed comparison of trajectories
    """
    trajectories = {
        src: build_character_trajectory(char_id, src)
        for src in source_ids
    }

    # Find all locations mentioned across sources
    all_locations: Dict[str, List[str]] = {}
    for src, traj in trajectories.items():
        for wp in traj.waypoints:
            if wp.location_id not in all_locations:
                all_locations[wp.location_id] = []
            if src not in all_locations[wp.location_id]:
                all_locations[wp.location_id].append(src)

    # Identify divergence points (location in some but not all)
    divergence_points = []
    convergence_points = []

    for loc_id, sources in all_locations.items():
        loc = get_location(loc_id)
        if len(sources) == len(source_ids):
            convergence_points.append({
                "location_id": loc_id,
                "location_name": loc.name if loc else loc_id,
                "sources": sources,
            })
        else:
            missing = [s for s in source_ids if s not in sources]
            divergence_points.append({
                "location_id": loc_id,
                "location_name": loc.name if loc else loc_id,
                "present_in": sources,
                "absent_from": missing,
            })

    # Calculate divergence score
    total_locs = len(all_locations)
    divergent_locs = len(divergence_points)
    divergence_score = divergent_locs / total_locs if total_locs > 0 else 0.0

    return TrajectoryComparison(
        character_id=char_id,
        sources=source_ids,
        divergence_points=divergence_points,
        convergence_points=convergence_points,
        total_divergence_score=round(divergence_score, 3),
    )


def generate_trajectory_geojson(
    char_id: str,
    source_id: str,
) -> Dict[str, Any]:
    """Generate GeoJSON for a character's trajectory.

    Can be used with mapping libraries (Leaflet, D3.js) for visualization.

    Parameters
    ----------
    char_id : str
        Character ID
    source_id : str
        Source to visualize

    Returns
    -------
    dict
        GeoJSON FeatureCollection
    """
    traj = build_character_trajectory(char_id, source_id)

    features = []

    # Add points for each waypoint
    for wp in traj.waypoints:
        loc = get_location(wp.location_id)
        if loc:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc.longitude, loc.latitude],
                },
                "properties": {
                    "sequence": wp.sequence,
                    "location": loc.name,
                    "reference": wp.reference,
                },
            })

    # Add LineString connecting waypoints
    coordinates = []
    for wp in traj.waypoints:
        loc = get_location(wp.location_id)
        if loc:
            coordinates.append([loc.longitude, loc.latitude])

    if len(coordinates) > 1:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates,
            },
            "properties": {
                "character": char_id,
                "source": source_id,
                "total_distance_km": traj.total_distance_km,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def generate_divergent_paths_data(
    char_id: str,
    source_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate data for visualizing divergent narrative paths.

    Creates structured data showing how different sources trace
    different geographic paths for the same character.

    Parameters
    ----------
    char_id : str
        Character ID
    source_ids : list of str, optional
        Sources to compare. Defaults to Synoptics + John.

    Returns
    -------
    dict
        Visualization data with paths per source
    """
    if source_ids is None:
        source_ids = ["mark", "matthew", "luke", "john"]

    paths: Dict[str, List[Dict[str, Any]]] = {}

    for src in source_ids:
        traj = build_character_trajectory(char_id, src)
        path_points = []

        for wp in traj.waypoints:
            loc = get_location(wp.location_id)
            if loc:
                path_points.append({
                    "sequence": wp.sequence,
                    "lat": loc.latitude,
                    "lng": loc.longitude,
                    "name": loc.name,
                    "reference": wp.reference,
                })

        paths[src] = path_points

    comparison = compare_trajectories(char_id, source_ids)

    return {
        "character_id": char_id,
        "paths": paths,
        "divergence_score": comparison.total_divergence_score,
        "divergence_points": comparison.divergence_points,
        "convergence_points": comparison.convergence_points,
        "visualization_hint": "Render each source path with different colors",
    }


def analyze_jerusalem_visits(char_id: str = "jesus") -> Dict[str, Any]:
    """Analyze Jerusalem visits across sources.

    A classic synoptic problem example: Mark/Matthew/Luke show
    one Jerusalem visit, while John shows multiple.

    Parameters
    ----------
    char_id : str
        Character ID (default: "jesus")

    Returns
    -------
    dict
        Analysis of Jerusalem visits per source
    """
    source_visits: Dict[str, int] = {}

    for src in ["mark", "matthew", "luke", "john"]:
        traj = build_character_trajectory(char_id, src)
        jerusalem_visits = sum(
            1 for wp in traj.waypoints
            if wp.location_id == "jerusalem"
        )
        source_visits[src] = jerusalem_visits

    return {
        "character_id": char_id,
        "location": "jerusalem",
        "visits_per_source": source_visits,
        "divergence_detected": len(set(source_visits.values())) > 1,
        "analysis": {
            "synoptic_pattern": source_visits.get("mark", 0),
            "johannine_pattern": source_visits.get("john", 0),
            "scholarly_note": (
                "John's multiple Jerusalem visits suggest either historical "
                "accuracy or theological structuring around Jewish festivals."
            ),
        },
    }


def get_narrative_sequence(
    source_id: str,
    event_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Get the narrative sequence of events in a source.

    Shows how a source orders events, useful for comparing
    narrative structure across gospels.

    Parameters
    ----------
    source_id : str
        Source to analyze
    event_ids : list of str, optional
        Events to sequence. If None, uses all events.

    Returns
    -------
    list of dict
        Events in narrative order with location data
    """
    if event_ids is None:
        event_ids = queries.list_event_ids()

    sequence = []

    for event_id in event_ids:
        try:
            event = queries.get_event(event_id)
            account = next(
                (a for a in event.accounts if a.source_id == source_id),
                None
            )

            if account:
                loc_id = _extract_location_from_reference(account.reference)
                loc = get_location(loc_id) if loc_id else None

                sequence.append({
                    "event_id": event_id,
                    "label": event.label,
                    "reference": account.reference,
                    "location_id": loc_id,
                    "location_name": loc.name if loc else None,
                    "coordinates": [loc.latitude, loc.longitude] if loc else None,
                })
        except Exception:
            continue

    return sequence
