"""SimBrief API integration for fetching flight plans.

SimBrief is a free flight planning service used by many flight simmers.
This module provides integration with the SimBrief API to fetch the latest
OFP (Operational Flight Plan) for a user.

API Documentation: https://www.simbrief.com/api/xml.fetcher.php
"""
import json
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree

from .models import Flightplan, Waypoint, WaypointType


@dataclass
class SimBriefOFP:
    """Represents a SimBrief Operational Flight Plan."""
    # Basic info
    flight_number: str
    departure_icao: str
    departure_name: str
    arrival_icao: str
    arrival_name: str
    alternate_icao: Optional[str]

    # Aircraft
    aircraft_icao: str
    aircraft_name: str
    aircraft_reg: str

    # Route
    route: str
    distance_nm: float
    flight_time_minutes: int

    # Altitudes
    initial_altitude: int  # feet
    cruise_altitude: int  # feet

    # Fuel
    fuel_plan_ramp: float  # lbs or kg
    fuel_unit: str  # "lbs" or "kgs"

    # Weights
    passengers: int
    cargo: float
    payload: float
    zfw: float  # Zero Fuel Weight
    tow: float  # Takeoff Weight
    ldw: float  # Landing Weight

    # Weather
    departure_metar: Optional[str]
    arrival_metar: Optional[str]

    # Waypoints
    waypoints: list[Waypoint]

    # Raw data
    ofp_id: str
    generated_at: str


class SimBriefClient:
    """Client for the SimBrief API."""

    API_URL = "https://www.simbrief.com/api/xml.fetcher.php"

    def __init__(self, pilot_id: Optional[str] = None):
        """
        Initialize the SimBrief client.

        Args:
            pilot_id: SimBrief pilot ID (numeric or username)
        """
        self.pilot_id = pilot_id
        self.last_error: Optional[str] = None

    def set_pilot_id(self, pilot_id: str):
        """Set the pilot ID."""
        self.pilot_id = (pilot_id or "").strip()

    def fetch_latest_ofp(self, pilot_id: Optional[str] = None) -> Optional[SimBriefOFP]:
        """
        Fetch the latest OFP for a pilot.

        Args:
            pilot_id: Optional pilot ID (uses instance pilot_id if not provided)

        Returns:
            SimBriefOFP if successful, None otherwise.
            On failure, self.last_error contains a user-facing message.
        """
        self.last_error = None
        pid = (pilot_id or self.pilot_id or "").strip()
        if not pid:
            self.last_error = "Pilot IDが設定されていません"
            return None

        # Numeric input is a Pilot ID (userid=), anything else is a
        # SimBrief username/alias (username=). Sending a username as
        # userid makes the API return HTTP 400.
        param = 'userid' if pid.isdigit() else 'username'
        url = f"{self.API_URL}?{param}={urllib.parse.quote(pid)}&json=1"

        try:
            request = urllib.request.Request(
                url, headers={'User-Agent': 'MSFS-Flightplan-Viewer/1.3'}
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                ofp = self._parse_ofp(data)
                if ofp is None and not self.last_error:
                    self.last_error = "OFPデータの解析に失敗しました"
                return ofp
        except urllib.error.HTTPError as e:
            self.last_error = self._describe_http_error(e)
            print(f"HTTP Error fetching SimBrief OFP: {e.code} ({self.last_error})")
            return None
        except urllib.error.URLError as e:
            self.last_error = f"SimBriefに接続できません（ネットワークエラー）: {e.reason}"
            print(f"URL Error fetching SimBrief OFP: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            self.last_error = "SimBriefの応答を解析できませんでした"
            print(f"JSON decode error: {e}")
            return None
        except Exception as e:
            self.last_error = f"予期しないエラー: {e}"
            print(f"Error fetching SimBrief OFP: {e}")
            return None

    def _describe_http_error(self, e: urllib.error.HTTPError) -> str:
        """Translate a SimBrief HTTP error into a user-facing message.

        SimBrief returns error details in the response body, e.g.
        {"fetch": {"status": "Error: Unknown UserID", ...}}
        """
        detail = ""
        try:
            body = json.loads(e.read().decode('utf-8'))
            detail = body.get('fetch', {}).get('status', '') or ''
        except Exception:
            pass

        detail_lower = detail.lower()
        if 'unknown userid' in detail_lower or 'unknown username' in detail_lower:
            return (
                "Pilot IDが見つかりません。\n"
                "SimBrief.com → Account Settings に表示される\n"
                "数字のPilot ID、またはユーザー名を確認してください"
            )
        if 'no flight plan' in detail_lower:
            return (
                "このアカウントにはフライトプランがありません。\n"
                "先にSimBrief.comでフライトプランを作成（Generate Flight）\n"
                "してください"
            )
        if detail:
            return f"SimBriefエラー: {detail}"
        return f"SimBrief APIエラー (HTTP {e.code})"

    def _parse_ofp(self, data: dict) -> Optional[SimBriefOFP]:
        """Parse the SimBrief API response into an OFP object."""
        try:
            # Check for errors (status is e.g. "Error: Unknown UserID")
            if 'fetch' in data and 'status' in data['fetch']:
                status = str(data['fetch']['status'] or '')
                if status.lower().startswith('error'):
                    self.last_error = f"SimBriefエラー: {status}"
                    print(f"SimBrief error: {status}")
                    return None

            # Extract sections
            params = data.get('params', {})
            general = data.get('general', {})
            origin = data.get('origin', {})
            destination = data.get('destination', {})
            alternate = data.get('alternate', {})
            aircraft = data.get('aircraft', {})
            fuel = data.get('fuel', {})
            weights = data.get('weights', {})
            times = data.get('times', {})
            navlog = data.get('navlog', {}) or {}
            weather = data.get('weather', {})

            # Parse waypoints from navlog
            waypoints = []
            fixes = navlog.get('fix', [])
            if isinstance(fixes, dict):
                fixes = [fixes]  # Single waypoint case

            for fix in fixes:
                ident = fix.get('ident', '')
                if not ident:
                    continue

                # Determine waypoint type
                fix_type = fix.get('type', '').upper()
                wpt_type = WaypointType.FIX
                if fix_type in ('APT', 'AIRPORT'):
                    wpt_type = WaypointType.AIRPORT
                elif fix_type == 'VOR':
                    wpt_type = WaypointType.VOR
                elif fix_type == 'NDB':
                    wpt_type = WaypointType.NDB
                elif fix_type in ('WPT', 'INT', 'FIX'):
                    wpt_type = WaypointType.FIX

                try:
                    lat = float(fix.get('pos_lat', 0))
                    lon = float(fix.get('pos_long', 0))
                    alt = int(fix.get('altitude_feet', 0)) if fix.get('altitude_feet') else None
                except (ValueError, TypeError):
                    lat, lon, alt = 0.0, 0.0, None

                waypoint = Waypoint(
                    ident=ident,
                    latitude=lat,
                    longitude=lon,
                    waypoint_type=wpt_type,
                    altitude=alt,
                    name=fix.get('name'),
                    airway=fix.get('via_airway') if fix.get('via_airway') != 'DCT' else None
                )
                waypoints.append(waypoint)

            # Parse flight time
            flight_time_str = times.get('est_time_enroute', '0000')
            try:
                hours = int(flight_time_str[:2]) if len(flight_time_str) >= 2 else 0
                minutes = int(flight_time_str[2:4]) if len(flight_time_str) >= 4 else 0
                flight_time_minutes = hours * 60 + minutes
            except ValueError:
                flight_time_minutes = 0

            # Build OFP
            ofp = SimBriefOFP(
                flight_number=general.get('flight_number', ''),
                departure_icao=origin.get('icao_code', ''),
                departure_name=origin.get('name', ''),
                arrival_icao=destination.get('icao_code', ''),
                arrival_name=destination.get('name', ''),
                alternate_icao=alternate.get('icao_code') if alternate else None,
                aircraft_icao=aircraft.get('icaocode', ''),
                aircraft_name=aircraft.get('name', ''),
                aircraft_reg=aircraft.get('reg', ''),
                route=general.get('route', ''),
                distance_nm=float(general.get('air_distance', 0)),
                flight_time_minutes=flight_time_minutes,
                initial_altitude=int(general.get('initial_altitude', 0)),
                cruise_altitude=int(general.get('cruise_altitude', 0)),
                fuel_plan_ramp=float(fuel.get('plan_ramp', 0)),
                fuel_unit=params.get('units', 'lbs'),
                passengers=int(weights.get('pax_count', 0)),
                cargo=float(weights.get('cargo', 0)),
                payload=float(weights.get('payload', 0)),
                zfw=float(weights.get('est_zfw', 0)),
                tow=float(weights.get('est_tow', 0)),
                ldw=float(weights.get('est_ldw', 0)),
                departure_metar=weather.get('orig_metar'),
                arrival_metar=weather.get('dest_metar'),
                waypoints=waypoints,
                ofp_id=params.get('request_id', ''),
                generated_at=params.get('time_generated', '')
            )

            return ofp

        except Exception as e:
            print(f"Error parsing SimBrief OFP: {e}")
            return None

    def ofp_to_flightplan(self, ofp: SimBriefOFP) -> Flightplan:
        """
        Convert a SimBrief OFP to a Flightplan object.

        Args:
            ofp: SimBrief OFP

        Returns:
            Flightplan object
        """
        # Create departure waypoint
        departure = Waypoint(
            ident=ofp.departure_icao,
            latitude=ofp.waypoints[0].latitude if ofp.waypoints else 0,
            longitude=ofp.waypoints[0].longitude if ofp.waypoints else 0,
            waypoint_type=WaypointType.AIRPORT,
            name=ofp.departure_name
        )

        # Create destination waypoint
        destination = Waypoint(
            ident=ofp.arrival_icao,
            latitude=ofp.waypoints[-1].latitude if ofp.waypoints else 0,
            longitude=ofp.waypoints[-1].longitude if ofp.waypoints else 0,
            waypoint_type=WaypointType.AIRPORT,
            name=ofp.arrival_name
        )

        # Get intermediate waypoints (excluding first and last)
        intermediate = []
        if len(ofp.waypoints) > 2:
            intermediate = ofp.waypoints[1:-1]

        flightplan = Flightplan(
            title=f"{ofp.flight_number} {ofp.departure_icao}-{ofp.arrival_icao}",
            departure=departure,
            destination=destination,
            waypoints=intermediate,
            cruise_altitude=ofp.cruise_altitude,
            aircraft_type=ofp.aircraft_icao,
            source_file=f"SimBrief OFP {ofp.ofp_id}"
        )

        return flightplan


@dataclass
class SimBriefSettings:
    """Settings for SimBrief integration."""
    pilot_id: str = ""
    auto_fetch: bool = False  # Auto-fetch on startup
    fetch_interval_minutes: int = 0  # 0 = disabled

    def is_configured(self) -> bool:
        """Check if SimBrief is configured."""
        return bool(self.pilot_id)
