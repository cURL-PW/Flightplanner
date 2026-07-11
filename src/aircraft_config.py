"""Aircraft configuration and flightplan path management."""
import os
from pathlib import Path

from .models import AircraftConfig


def get_msfs_base_paths() -> list[Path]:
    """Get possible MSFS installation base paths."""
    paths = []

    # Windows Store version
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if local_app_data:
        store_path = Path(local_app_data) / 'Packages' / 'Microsoft.FlightSimulator_8wekyb3d8bbwe' / 'LocalState'
        if store_path.exists():
            paths.append(store_path)

    # Steam version
    app_data = os.environ.get('APPDATA', '')
    if app_data:
        steam_path = Path(app_data) / 'Microsoft Flight Simulator'
        if steam_path.exists():
            paths.append(steam_path)

    # Custom path from environment
    custom_path = os.environ.get('MSFS_PATH', '')
    if custom_path:
        custom = Path(custom_path)
        if custom.exists():
            paths.append(custom)

    return paths


def get_community_folder() -> Path | None:
    """Get the MSFS Community folder path."""
    for base in get_msfs_base_paths():
        community = base / 'packages' / 'Community'
        if community.exists():
            return community

        # Alternative location
        community_alt = base / 'Community'
        if community_alt.exists():
            return community_alt

    return None


def get_default_aircraft_configs() -> list[AircraftConfig]:
    """Get default aircraft configurations with their flightplan paths."""

    configs = []
    base_paths = get_msfs_base_paths()
    community = get_community_folder()

    # Local AppData for addon-specific folders
    local_app_data = os.environ.get('LOCALAPPDATA', '')

    # ============================================================
    # MSFS Default Aircraft (B787, A320neo, etc.)
    # ============================================================
    msfs_default_paths = []
    for base in base_paths:
        # Default flightplan storage location
        msfs_default_paths.append(str(base))
        # Custom flightplan folders
        fp_folder = base / 'flightplans'
        if fp_folder.exists():
            msfs_default_paths.append(str(fp_folder))

    configs.append(AircraftConfig(
        name="Default Aircraft (B787, A320neo, etc.)",
        manufacturer="Microsoft/Asobo",
        flightplan_paths=msfs_default_paths,
        supported_formats=['.pln'],
        icon="default"
    ))

    # ============================================================
    # PMDG Aircraft (737, 777, 747)
    # ============================================================
    pmdg_paths = []

    # PMDG stores flightplans in their work folders
    pmdg_aircraft = [
        'pmdg-aircraft-737',
        'pmdg-aircraft-777',
        'pmdg-aircraft-747',
        'pmdg-737',
        'pmdg-777',
        'pmdg-747',
    ]

    for base in base_paths:
        packages = base / 'packages'
        if packages.exists():
            for aircraft in pmdg_aircraft:
                work_folder = packages / aircraft / 'work' / 'Flightplans'
                if work_folder.exists():
                    pmdg_paths.append(str(work_folder))

    if community:
        for aircraft in pmdg_aircraft:
            work_folder = community / aircraft / 'work' / 'Flightplans'
            if work_folder.exists():
                pmdg_paths.append(str(work_folder))

    # PMDG Operations Center path
    if local_app_data:
        pmdg_ops = Path(local_app_data) / 'PMDG' / 'Flightplans'
        if pmdg_ops.exists():
            pmdg_paths.append(str(pmdg_ops))

    configs.append(AircraftConfig(
        name="737/777/747 Series",
        manufacturer="PMDG",
        flightplan_paths=pmdg_paths,
        supported_formats=['.pln', '.rte'],
        icon="pmdg"
    ))

    # ============================================================
    # Fenix A320 Series
    # ============================================================
    fenix_paths = []

    if local_app_data:
        # Fenix stores flightplans in LocalAppData
        fenix_base = Path(local_app_data) / 'Fenix'
        if fenix_base.exists():
            # A320 variants
            for variant in ['A320', 'A319', 'A321', 'A3XX']:
                variant_path = fenix_base / variant / 'Flightplans'
                if variant_path.exists():
                    fenix_paths.append(str(variant_path))

            # Also check the base Fenix folder
            fenix_fp = fenix_base / 'Flightplans'
            if fenix_fp.exists():
                fenix_paths.append(str(fenix_fp))

    # Fenix also uses SimBrief integration
    if local_app_data:
        simbrief = Path(local_app_data) / 'SimBrief'
        if simbrief.exists():
            fenix_paths.append(str(simbrief))

    configs.append(AircraftConfig(
        name="A320 Series (A319/A320/A321)",
        manufacturer="Fenix",
        flightplan_paths=fenix_paths,
        supported_formats=['.flp', '.pln'],
        icon="fenix"
    ))

    # ============================================================
    # FlyByWire A32NX
    # ============================================================
    fbw_paths = []

    if community:
        # FlyByWire aircraft folder
        fbw_variants = ['flybywire-aircraft-a320-neo', 'a32nx']
        for variant in fbw_variants:
            fbw_folder = community / variant
            if fbw_folder.exists():
                fbw_paths.append(str(fbw_folder))

    # FBW also uses default MSFS flightplan locations
    for base in base_paths:
        fbw_paths.append(str(base))

    configs.append(AircraftConfig(
        name="A32NX (A320neo)",
        manufacturer="FlyByWire",
        flightplan_paths=fbw_paths,
        supported_formats=['.flp', '.pln'],
        icon="fbw"
    ))

    # ============================================================
    # iniBuilds A300/A310 (Note: ToLiss is X-Plane only)
    # ============================================================
    ini_paths = []

    if community:
        ini_aircraft = ['inibuilds-a300', 'inibuilds-a310', 'inibuilds-a380']
        for aircraft in ini_aircraft:
            aircraft_folder = community / aircraft
            if aircraft_folder.exists():
                ini_paths.append(str(aircraft_folder))

    if local_app_data:
        ini_folder = Path(local_app_data) / 'iniBuilds'
        if ini_folder.exists():
            ini_paths.append(str(ini_folder))

    configs.append(AircraftConfig(
        name="A300/A310/A380 Series",
        manufacturer="iniBuilds",
        flightplan_paths=ini_paths,
        supported_formats=['.pln', '.flp'],
        icon="ini"
    ))

    # ============================================================
    # Aerosoft CRJ Series
    # ============================================================
    aerosoft_paths = []

    if community:
        aerosoft_aircraft = ['aerosoft-crj', 'aerosoft-aircraft-crj-550-700', 'aerosoft-aircraft-crj-900-1000']
        for aircraft in aerosoft_aircraft:
            aircraft_folder = community / aircraft / 'SimObjects' / 'Airplanes'
            if aircraft_folder.exists():
                aerosoft_paths.append(str(aircraft_folder.parent.parent))

    # Aerosoft also uses a dedicated folder
    if local_app_data:
        aerosoft_folder = Path(local_app_data) / 'Aerosoft'
        crj_folder = aerosoft_folder / 'CRJ' / 'Flightplans'
        if crj_folder.exists():
            aerosoft_paths.append(str(crj_folder))

    configs.append(AircraftConfig(
        name="CRJ Series",
        manufacturer="Aerosoft",
        flightplan_paths=aerosoft_paths,
        supported_formats=['.flp', '.pln'],
        icon="aerosoft"
    ))

    # ============================================================
    # Leonardo Maddog MD-80
    # ============================================================
    maddog_paths = []

    if local_app_data:
        maddog_folder = Path(local_app_data) / 'Leonardo' / 'MD-80' / 'Flightplans'
        if maddog_folder.exists():
            maddog_paths.append(str(maddog_folder))

    configs.append(AircraftConfig(
        name="MD-80 Series",
        manufacturer="Leonardo/Maddog",
        flightplan_paths=maddog_paths,
        supported_formats=['.pln', '.rte'],
        icon="maddog"
    ))

    # ============================================================
    # Headwind A339X
    # ============================================================
    headwind_paths = []

    if community:
        headwind_folder = community / 'headwind-aircraft-a330-900'
        if headwind_folder.exists():
            headwind_paths.append(str(headwind_folder))

    configs.append(AircraftConfig(
        name="A330-900",
        manufacturer="Headwind",
        flightplan_paths=headwind_paths,
        supported_formats=['.pln', '.flp'],
        icon="headwind"
    ))

    # ============================================================
    # LVFR / LatinVFR aircraft
    # ============================================================
    lvfr_paths = []

    if community:
        lvfr_aircraft = ['latinvfr-a340', 'lvfr-a340']
        for aircraft in lvfr_aircraft:
            aircraft_folder = community / aircraft
            if aircraft_folder.exists():
                lvfr_paths.append(str(aircraft_folder))

    configs.append(AircraftConfig(
        name="A340 Series",
        manufacturer="LatinVFR",
        flightplan_paths=lvfr_paths,
        supported_formats=['.pln'],
        icon="lvfr"
    ))

    # ============================================================
    # Custom/General folder for manual imports
    # ============================================================
    custom_paths = []
    home = os.environ.get('USERPROFILE', os.environ.get('HOME', ''))
    if home:
        docs = Path(home) / 'Documents' / 'MSFS Flightplans'
        custom_paths.append(str(docs))
        downloads = Path(home) / 'Downloads'
        if downloads.exists():
            custom_paths.append(str(downloads))

    configs.append(AircraftConfig(
        name="Custom / Imported Flightplans",
        manufacturer="User",
        flightplan_paths=custom_paths,
        supported_formats=['.pln', '.flp', '.rte'],
        icon="custom"
    ))

    return configs


class AircraftManager:
    """Manages aircraft configurations and flightplan discovery."""

    def __init__(self):
        self.configs = get_default_aircraft_configs()
        self.custom_paths: list[Path] = []

    def add_custom_path(self, path: Path) -> None:
        """Add a custom flightplan search path."""
        if path not in self.custom_paths:
            self.custom_paths.append(path)

    def get_all_flightplan_files(self) -> list[tuple[Path, AircraftConfig]]:
        """Get all flightplan files from all configured paths."""
        files = []

        for config in self.configs:
            for path_str in config.flightplan_paths:
                path = Path(path_str)
                if path.exists():
                    for ext in config.supported_formats:
                        for fp_file in path.rglob(f'*{ext}'):
                            files.append((fp_file, config))

        # Also search custom paths
        for path in self.custom_paths:
            if path.exists():
                for ext in ['.pln', '.flp', '.rte']:
                    for fp_file in path.rglob(f'*{ext}'):
                        # Associate with custom config
                        custom_config = self.configs[-1]  # Last config is custom
                        files.append((fp_file, custom_config))

        return files

    def get_flightplan_files_for_aircraft(self, config: AircraftConfig) -> list[Path]:
        """Get all flightplan files for a specific aircraft configuration."""
        files = []

        for path_str in config.flightplan_paths:
            path = Path(path_str)
            if path.exists():
                for ext in config.supported_formats:
                    files.extend(path.rglob(f'*{ext}'))

        return files
