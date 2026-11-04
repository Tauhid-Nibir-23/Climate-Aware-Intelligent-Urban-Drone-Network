# FINAL PROJECT REVIEW REPORT — PHASE 7.3 (READ-ONLY AUDIT)

**Project:** Climate-Aware Intelligent Urban Drone Network  
**Study Area:** PSTU Main Campus (`DEPOT-PSTU`) & Dumki Upazila, Patuakhali, Bangladesh  
**Course:** Simulation and Modeling  
**Review Date:** November 4, 2026  
**Audit Mode:** Strictly Read-Only Inspection & Non-Destructive Execution (`0` existing project files modified)

---

## 1. Files Successfully Found

All expected Phase 7.2 project directories, source modules, spatial data files, automated tests, benchmark outputs, and academic/viva deliverables were verified on disk under `d:\Projects\Simulation` (`41` tracked/project files, excluding `.git`, `.pytest_cache`, and `__pycache__`):

### Root Application, Launchers & Documentation (9 files)
| File Path | Size (Bytes) | Status |
| :--- | ---: | :--- |
| `app.py` | 16,758 | Found |
| `README.md` | 2,113 | Found |
| `requirements.txt` | 78 | Found |
| `run.bat` | 135 | Found |
| `run_app.py` | 330 | Found |
| `AUDIT_REPORT.md` | 44,569 | Found |
| `PROJECT_REPORT.md` | 47,403 | Found |
| `VIVA_PREP.md` | 17,057 | Found |
| `PRESENTATION_OUTLINE.md` | 15,201 | Found |

### Core Source Package — `src/` (9 files)
| File Path | Size (Bytes) | Role |
| :--- | ---: | :--- |
| `src/__init__.py` | 42 | Package docstring marker |
| `src/config.py` | 2,671 | `DroneSpecs`, `WeatherScenario`, `WEATHER_SCENARIOS` |
| `src/models.py` | 4,526 | `DroneStatus`, `DeliveryRequest`, `Battery`, `Drone` |
| `src/network.py` | 2,926 | `haversine_distance()`, `DumkiNetwork` (`networkx.Graph`) |
| `src/generator.py` | 1,601 | Seeded Poisson order stream generator (`generate_synthetic_requests()`) |
| `src/algorithms.py` | 4,744 | `BaseDispatcher`, `FCFSDispatcher`, `BatteryAwareDispatcher` (BAPA) |
| `src/simulation.py` | 14,005 | SimPy DES engine (`DroneDeliverySimulation`), charging queue, metrics |
| `src/map_view.py` | 5,522 | Interactive Folium/Leaflet map builder (`build_dumki_folium_map()`) |
| `src/radar_view.py` | 21,142 | HTML5 Canvas 2D mission radar builder (`generate_radar_theater_html()`) |

### Data & Assets — `data/`, `assets/` (4 files)
| File Path | Size (Bytes) | Role |
| :--- | ---: | :--- |
| `data/dumki_nodes.json` | 2,902 | Coordinates/metadata for `DEPOT-PSTU` + 10 Dumki/PSTU delivery nodes |
| `data/boundaries/README.md` | 296 | Note explaining intentional omission of unverified boundary GeoJSON |
| `data/demo/README.md` | 119 | Legacy demo note |
| `assets/.gitkeep` | 1 | Empty directory placeholder |

### Automated Test Suite — `tests/` (8 files: 1 fixture file + 7 test modules = 29 tests)
| File Path | Size (Bytes) | Test Count |
| :--- | ---: | :---: |
| `tests/conftest.py` | 1,704 | Shared fixtures (`0` tests) |
| `tests/test_algorithms.py` | 3,779 | 5 |
| `tests/test_battery.py` | 5,216 | 5 |
| `tests/test_charging.py` | 3,927 | 3 |
| `tests/test_dispatch.py` | 5,623 | 4 |
| `tests/test_drone.py` | 4,367 | 5 |
| `tests/test_metrics.py` | 5,588 | 3 |
| `tests/test_simulation.py` | 7,034 | 4 |

### Multi-Seed Benchmark Outputs — `results/` (4 files)
| File Path | Size (Bytes) | Role |
| :--- | ---: | :--- |
| `results/run_benchmark_experiments.py` | 16,087 | Multi-seed paired experiment runner |
| `results/benchmark_per_seed.csv` | 13,290 | 60 per-seed simulation rows + header |
| `results/benchmark_aggregated.csv` | 3,290 | 12 aggregated `mean`/`std` summary rows + header |
| `results/EXPERIMENTAL_ANALYSIS.md` | 11,109 | Formatted experimental comparison & limitations |

### Archived Legacy Prototype — `archive_legacy_heat_explorer/` (7 files)
- `app_heat_explorer.py`, `charts.py`, `demo_simulation.py`, `geographic_data.py`, `heatmap.py`, `landsat_loader.py`, `statistics.py` (cleanly isolated from active imports).

---

## 2. Verified Working Components

Every item below is **verified by direct source inspection and code execution** (not assumed from `AUDIT_REPORT.md`):

1. **SimPy Process-Based Discrete-Event Simulation (`src/simulation.py`):**
   - Uses `simpy.Environment()` (`line 51`), `simpy.Resource(self.env, capacity=self.num_charging_bays)` (`line 52`), and three generator processes (`_order_arrival_process`, `_dispatch_scheduler_process`, `_drone_mission_process`). Contains zero `time.sleep()` calls; advances strictly along scheduled event timestamps (`self.env.now`).
2. **Synchronous Dispatch Concurrency Lock (`src/simulation.py:98-108`):**
   - Immediately upon selecting a drone inside `_dispatch_scheduler_process`, the scheduler removes `req` from `pending_orders` and synchronously sets `selected_drone.status = DroneStatus.OUTBOUND_DELIVERY` and `selected_drone.current_request_id = req.request_id` before spawning `_drone_mission_process`. Verified by `test_bug1_regression_no_duplicate_simultaneous_assignment` and multi-order batch tests that simultaneous arrivals never double-book a single drone.
3. **FCFS vs. BAPA Dispatch Algorithms (`src/algorithms.py`):**
   - `FCFSDispatcher` (`lines 25-53`) selects the first idle depot drone with `current_soc > 0.0` and `package_weight_kg <= 2.5` (`available_drones[0]`), ignoring round-trip energy and weather.
   - `BatteryAwareDispatcher` (`lines 54-123`) calculates exact outbound loaded energy (`payload_kg = request.package_weight_kg`) plus inbound empty energy (`payload_kg = 0.0`) scaled by `weather.climate_multiplier`, enforces the hard safety reserve (`projected_final_soc >= 0.20`), holds infeasible orders in queue (`return None`), and sorts feasible drones ascending by `projected_final_soc` (`line 121`) to select the best-fit minimum-surplus drone.
4. **Battery Physics, Input Validation & Climate Scaling (`src/models.py:34-96`, `src/config.py:13-64`):**
   - `Battery` clamps `current_soc` to `[0.0, 1.0]`, raises `ValueError` on negative energy/distance/payload or non-positive capacity/speed/climate multiplier, and computes leg energy in Watt-hours accurately (`27.81 Wh` empty 5 km; `42.70 Wh` with 2.5 kg; `60.00 Wh` under `1.405x` Extreme Heatwave).
   - `WeatherScenario.climate_multiplier` evaluates to `1.06` (`Temperate`), `1.18` (`Moderate Summer`), and `1.405` (`Extreme Heatwave`).
5. **Charging Station FIFO Queue & Threshold Logic (`src/simulation.py:203-224`):**
   - Returning drones with `current_soc < recharge_threshold_soc` (`0.50` default) transition to `WAITING_FOR_CHARGER`, queue in FIFO order on `simpy.Resource`, record exact queue waiting time (`wait_duration = self.env.now - wait_start`), recharge linearly to `1.0` SoC at effective power `300 W * 0.90 = 270 W`, and return to `IDLE`. Drones returning at `>= recharge_threshold_soc` bypass the charger cleanly.
6. **Delivery Success vs. Mission Success Accounting (`src/simulation.py:138-201, 232-280`):**
   - Customer delivery outcomes (`completed_orders` vs. `failed_orders`) and vehicle round-trip outcomes (`completed_missions` vs. `failed_missions` / `return_failures`) are tracked separately without double-counting. On return-leg battery exhaustion (`RETURN_FAILED`), `delivered_orders` increments once, `failed_orders` stays `0`, and `return_failures`, `failed_missions`, and `failed_drones` increment once.
7. **Dumki & PSTU Spatial Network (`src/network.py`, `data/dumki_nodes.json`):**
   - Loads `DEPOT-PSTU` (`22.4648°N, 90.3835°E`) and 10 delivery nodes (`4` campus nodes at `0.204–0.508 km`; `6` regional nodes at `1.321–5.336 km`) into a complete `networkx.Graph` weighted by `haversine_distance()`.
8. **Dashboard Builders & Syntax (`app.py`, `src/map_view.py`, `src/radar_view.py`):**
   - All 19 active Python files pass `compile()` / AST parsing cleanly under Python `3.14.6`.
   - `build_dumki_folium_map()` executes cleanly in both `"PSTU Campus View"` and `"Full Dumki Regional View"`, generating a `44,555`-character Leaflet HTML map with 3 tile layers, markers, popups, and flight corridors.
   - `generate_radar_theater_html()` executes cleanly on live `DroneDeliverySimulation` event logs, generating a `43,441`-character HTML5 Canvas visualization embedding real simulation events (`141` events in default 240-min run).
   - `app.py` implements all required tabs (`2D Live Mission Radar`, `Interactive Real-World Map`, `Benchmark Experiment` with separate delivery/mission success cards, return-leg failures, grouped Plotly charts, and fleet telemetry, `Discrete-Event Logs` with CSV export, and `Architecture & Viva Prep`), using `width="stretch"` with zero deprecated `use_container_width` calls.
   - *Evidence boundary note:* Live browser rendering and socket binding (`streamlit run`) could not be interactively opened inside the network-isolated terminal sandbox (`127.0.0.1` port binding is blocked by sandbox isolation); therefore, browser interactivity (clicking map markers, scrubbing the HTML5 canvas slider in Chrome/Edge) is verified by static code inspection + HTML generation rather than live GUI clicks.
9. **Automated Test Suite (`tests/`) & Reproducible Benchmark Runner (`results/`):**
   - All `29` `pytest` unit and regression tests pass (`29 passed in 3.45s`).
   - Re-executing `run_all_experiments()` in memory reproduced `results/benchmark_per_seed.csv` (`60` rows × `26` cols), `results/benchmark_aggregated.csv` (`12` rows × `34` cols), and `results/EXPERIMENTAL_ANALYSIS.md` with **zero numerical or text differences**.

---

## 3. Actual Commands Executed and Their Outputs

### Command 1 — Workspace Directory & File Inventory
```powershell
Get-ChildItem -Force d:\Projects\Simulation | Select-Object Mode, LastWriteTime, Length, Name
Get-ChildItem -Recurse -File d:\Projects\Simulation | Where-Object { $_.FullName -notmatch '\\(\.venv|venv|__pycache__|\.git|\.pytest_cache)\\' } | Select-Object FullName, Length, LastWriteTime
```
- **Exit Code:** `0`
- **Verified Output Summary:** Confirmed `app.py`, `PROJECT_REPORT.md`, `VIVA_PREP.md`, `PRESENTATION_OUTLINE.md`, `AUDIT_REPORT.md`, `README.md`, `requirements.txt`, `run.bat`, `run_app.py`, `data/dumki_nodes.json`, 9 files in `src/`, 8 files in `tests/`, 4 files in `results/`, and 7 archived files in `archive_legacy_heat_explorer/`.

### Command 2 — Automated Pytest Suite Execution (Read-Only, Cache Disabled)
```powershell
python --version; python -m pytest -v -p no:cacheprovider
```
- **Exit Code:** `0`
- **Actual Output:**
```text
Python 3.14.6
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- C:\Program Files\Python314\python.exe
rootdir: D:\Projects\Simulation
plugins: anyio-4.14.2
collecting ... collected 29 items

tests/test_algorithms.py::test_base_dispatcher_raises_not_implemented PASSED [  3%]
tests/test_algorithms.py::test_fcfs_selects_first_idle_drone_at_depot PASSED [  6%]
tests/test_algorithms.py::test_bapa_best_fit_minimum_surplus_selection PASSED [ 10%]
tests/test_algorithms.py::test_payload_capacity_constraint_enforced PASSED [ 13%]
tests/test_algorithms.py::test_spatial_network_direct_corridor_distances PASSED [ 17%]
tests/test_battery.py::test_battery_decreases_after_flight PASSED        [ 20%]
tests/test_battery.py::test_battery_payload_and_climate_scaling PASSED   [ 24%]
tests/test_battery.py::test_battery_cannot_exceed_capacity PASSED        [ 27%]
tests/test_battery.py::test_invalid_negative_energy_is_handled PASSED    [ 31%]
tests/test_battery.py::test_reserve_constraint_and_insufficient_battery_prevents_infeasible_mission PASSED [ 34%]
tests/test_charging.py::test_charging_triggered_below_threshold_and_recharges_to_full PASSED [ 37%]
tests/test_charging.py::test_charging_bay_capacity_and_queue_wait_time PASSED [ 41%]
tests/test_charging.py::test_charging_skipped_when_soc_above_threshold PASSED [ 44%]
tests/test_dispatch.py::test_bug1_regression_no_duplicate_simultaneous_assignment PASSED [ 48%]
tests/test_dispatch.py::test_simultaneous_requests_sequential_completion_with_single_drone PASSED [ 51%]
tests/test_dispatch.py::test_multiple_simultaneous_requests_across_multi_drone_fleet PASSED [ 55%]
tests/test_dispatch.py::test_fcfs_vs_bapa_infeasible_order_queue_holding PASSED [ 58%]
tests/test_drone.py::test_initial_drone_state PASSED                     [ 62%]
tests/test_drone.py::test_valid_state_transitions PASSED                 [ 65%]
tests/test_drone.py::test_drone_availability_with_active_request PASSED  [ 68%]
tests/test_drone.py::test_mission_assignment_locks_drone_immediately PASSED [ 72%]
tests/test_drone.py::test_mission_completion_restores_drone_to_idle PASSED [ 75%]
tests/test_metrics.py::test_metrics_calculations_normal_delivery PASSED  [ 79%]
tests/test_metrics.py::test_metrics_failed_delivery_and_mutual_exclusivity PASSED [ 82%]
tests/test_metrics.py::test_metrics_empty_requests_zero_division_safety PASSED [ 86%]
tests/test_simulation.py::test_simulation_clock_advances_and_processes_requests PASSED [ 89%]
tests/test_simulation.py::test_bug2_regression_return_leg_failure_accounting PASSED [ 93%]
tests/test_simulation.py::test_outbound_leg_failure_accounting PASSED    [ 96%]
tests/test_simulation.py::test_reproducibility_with_fixed_random_seed PASSED [100%]

============================= 29 passed in 3.45s ==============================
```

### Command 3 — Independent Pure-Python Audit Verification (Imports, Physics, Map/Radar Builders, 60-Run CSV Reproduction & Failure Telemetry)
Executed via `python -u -B` (zero bytecode written to workspace; zero workspace files modified):
- **Exit Code:** `0`
- **Actual Output:**
```text
=== 1. PACKAGE VERSIONS (INSTALLED VS REQUIREMENTS.TXT) ===
  streamlit           : 1.66.1
  plotly              : 7.1.0
  simpy               : 4.1.2
  networkx            : 3.7
  pandas              : 3.0.3
  numpy               : 2.5.1
  folium              : 0.20.0
  streamlit-folium    : 0.27.4
  pytest              : 9.1.1

=== 2. THIRD-PARTY IMPORTS IN ACTIVE CODEBASE ===
  app.py                                : ['pandas', 'plotly', 'streamlit', 'streamlit_folium']
  results\run_benchmark_experiments.py  : ['pandas']
  src\map_view.py                       : ['folium']
  src\network.py                        : ['networkx']
  src\simulation.py                     : ['pandas', 'simpy']
  tests\conftest.py                     : ['pytest']
  tests\test_algorithms.py              : ['pytest']
  tests\test_battery.py                 : ['pytest']
  tests\test_charging.py                : ['pytest']
  tests\test_metrics.py                 : ['pytest']

=== 3. SPATIAL NETWORK & PHYSICS EQUATION CHECKS ===
  LOC-PSTU-CSE     | raw=0.220248 km | edge=0.220 km | leg=1.31 min
  LOC-PSTU-MED     | raw=0.203869 km | edge=0.204 km | leg=1.28 min
  LOC-PSTU-HALLS   | raw=0.354710 km | edge=0.355 km | leg=1.49 min
  LOC-PSTU-AGRI    | raw=0.507854 km | edge=0.508 km | leg=1.71 min
  LOC-DUMKI-HOSP   | raw=1.321123 km | edge=1.321 km | leg=2.83 min
  LOC-DUMKI-BAZAR  | raw=1.687548 km | edge=1.688 km | leg=3.34 min
  LOC-LEBUKHALI    | raw=4.219466 km | edge=4.219 km | leg=6.86 min
  LOC-MURADIA      | raw=3.690583 km | edge=3.691 km | leg=6.13 min
  LOC-PANGASHIA    | raw=4.632428 km | edge=4.632 km | leg=7.43 min
  LOC-ANGARIA      | raw=5.336451 km | edge=5.336 km | leg=8.41 min
  Weather 'Temperate (Spring/Winter)' (Temperate): T=26.0C, v=2.0m/s -> mult=1.06
  Weather 'Moderate Summer' (Moderate Summer): T=32.0C, v=4.0m/s -> mult=1.18
  Weather 'Extreme Monsoon / Heatwave' (Extreme Heatwave): T=39.0C, v=8.0m/s -> mult=1.405
  LOC-ANGARIA Extreme (2.5kg): out=63.52 Wh (35.3%), ret=41.36 Wh (23.0%), total=104.88 Wh (58.3%)

=== 4. MAP & RADAR COMPONENT GENERATION CHECK ===
  Folium map generated: campus HTML length = 44555 chars, regional object = Map
  Radar HTML generated: length = 43441 chars, events embedded = 141

=== 5. BENCHMARK CSV REPRODUCTION & ACCOUNTING CHECK ===
  [PASS] benchmark_per_seed.csv matches live simulation 100% identically (60 rows, 26 cols).
  [PASS] benchmark_aggregated.csv matches live aggregation 100% identically (12 rows, 34 cols).
  [PASS] EXPERIMENTAL_ANALYSIS.md matches generated report 100% identically.
  Order/Mission horizon cutoff discrepancies across 60 runs: []

=== 6. INSPECT SEED 202 FCFS RETURN-LEG FAILURE TELEMETRY ===
  Failed drone DRONE-04: status=FAILED_OUT_OF_BATTERY, deliv=3, comp_mis=2, fail_mis=1, energy=181.97Wh, final_soc=0.000
    t= 61.00 | MISSION_DISPATCH     | soc=1.000 | Departing to LOC-MURADIA with REQ-007
    t= 67.13 | PACKAGE_DELIVERED    | soc=0.795 | Package REQ-007 delivered at LOC-MURADIA
    t= 73.25 | RETURNED_TO_DEPOT    | soc=0.628 | Safely returned to depot with SoC: 62.8%
    t= 73.25 | DRONE_AVAILABLE      | soc=0.628 | Drone back in IDLE status at depot
    t=153.00 | MISSION_DISPATCH     | soc=0.628 | Departing to LOC-PSTU-MED with REQ-016
    t=154.28 | PACKAGE_DELIVERED    | soc=0.575 | Package REQ-016 delivered at LOC-PSTU-MED
    t=155.57 | RETURNED_TO_DEPOT    | soc=0.540 | Safely returned to depot with SoC: 54.0%
    t=155.57 | DRONE_AVAILABLE      | soc=0.540 | Drone back in IDLE status at depot
    t=160.00 | MISSION_DISPATCH     | soc=0.540 | Departing to LOC-ANGARIA with REQ-018
    t=168.41 | PACKAGE_DELIVERED    | soc=0.219 | Package REQ-018 delivered at LOC-ANGARIA
    t=176.82 | RETURN_FAILED        | soc=0.000 | Battery died on return journey to depot!
```

### Command 4 — Sandboxed Headless Server Probe & Git Cleanliness Verification
```powershell
git status --short
```
- **Server Probe Note:** Attempting to bind `127.0.0.1:8517` or run `streamlit.testing.v1.AppTest` inside the network-isolated execution sandbox blocked on local socket binding (`Unable to connect to the remote server`), confirming expected sandbox network isolation rather than an application syntax error.
- **Git Status Output:** Empty (`exit code 0`), confirming zero existing project files were modified prior to writing `FINAL_REVIEW_REPORT.md`.

---

## 4. Issues or Inconsistencies Found

### A. Packaging & Dependency Issues
1. **Missing Required Runtime Dependencies in `requirements.txt` (High / Critical for Fresh Installs):**
   - `app.py:10` imports `from streamlit_folium import st_folium` and `src/map_view.py:6` imports `import folium`.
   - `requirements.txt` currently lists only `streamlit`, `plotly`, `simpy`, `networkx`, `pandas`, and `numpy`—omitting **`folium`** and **`streamlit-folium`** (as well as **`pytest`** for running `tests/`). While pre-installed on the development machine, running `pip install -r requirements.txt` on an instructor's or evaluator's clean Python environment will cause `app.py` to crash immediately with `ModuleNotFoundError: No module named 'streamlit_folium'`.
   - Conversely, `numpy>=1.24` is listed in `requirements.txt` even though no active module outside `archive_legacy_heat_explorer/` imports `numpy` directly (harmless since `pandas` depends on it).

### B. Documentation & Metadata Inconsistencies
2. **Unfilled Title-Page / Slide Placeholders (`PROJECT_REPORT.md:14-21`, `PRESENTATION_OUTLINE.md:15-16`):**
   - Placeholder brackets (`[CSE-3XX / Enter Course Code]`, `[Enter Student Name]`, `[Enter Student ID / Registration Number]`, `[Level-3, Semester-X / Academic Year]`, `[Enter Supervisor Name, Designation]`) remain to be filled in before submission.
3. **Residual Legacy "Urban Heat Monitoring" Subtitle (`PROJECT_REPORT.md:3, 12`, `PRESENTATION_OUTLINE.md:13`):**
   - Both files carry the subtitle *"An Integrated Simulation Framework for **Urban Heat Monitoring** and Battery-Aware Multi-Drone Delivery Optimization..."*, whereas `README.md:3` was already updated to *"An Integrated Simulation Framework for Battery-Aware Multi-Drone Delivery Optimization"*. Because urban heat monitoring (`archive_legacy_heat_explorer/`) is explicitly out of scope of the active drone delivery simulation, keeping "Urban Heat Monitoring" in the main report and slide subtitle creates an unnecessary contradiction during viva questioning.
4. **Outdated Depot Identity & File List in `README.md` (`README.md:17, 37-45`) and Legacy Docstring in `src/__init__.py:1`:**
   - `README.md:17` states: *"Central depot at **Dumki Upazila Health Complex** serving rural clinics and union council posts."* In the actual system (`data/dumki_nodes.json`, `app.py`, `PROJECT_REPORT.md`), the central depot is **`DEPOT-PSTU` (PSTU Central Drone Command & Charging Hub)**, while `Dumki Upazila Health Complex` (`LOC-DUMKI-HOSP`) is a delivery destination `1.321 km` away.
   - `README.md:37-45` omits `src/map_view.py`, `src/radar_view.py`, `tests/`, `results/`, `PROJECT_REPORT.md`, `VIVA_PREP.md`, and `PRESENTATION_OUTLINE.md`.
   - `src/__init__.py:1` still contains `"""Modules for the Dumki UHI Explorer."""`.
5. **Minor Text/Comment Discrepancies:**
   - `VIVA_PREP.md:180` mentions *"29 automated unit and regression tests across 8 test modules"* and then lists 7 `test_*.py` files in parentheses (`tests/conftest.py` is the 8th file, holding fixtures rather than test functions).
   - `VIVA_PREP.md:145` has a minor spacing typo (`$\text{SoC}$.Occupying`).
   - `src/config.py:38` docstring states `Reference baseline: 25°C, 0 m/s headwind -> multiplier = 1.0`, while line 41 implements `0.015 * max(0.0, self.ambient_temp_c - 28.0)` (consistent at `25°C` since `max(0, -3) = 0`, though the actual penalty threshold is `28.0°C`, as accurately documented in `PROJECT_REPORT.md` Eq. 9.4).
   - Queueing notation varies slightly between `$M/M/c$` (`README.md:19`, `app.py:371`) and `$M/G/c$-style` (`PROJECT_REPORT.md:29`, `PRESENTATION_OUTLINE.md:41`); `$M/G/c$-style` is more exact since charging time is a deterministic function of returning SoC rather than exponential.

### C. Simulation & Dashboard Edge-Case Observations
6. **Full-Leg Energy/Distance/Time Accounting on Mid-Air Crash Legs (`src/simulation.py:131-137, 172-177`):**
   - When a drone runs out of battery on an outbound or return leg (`not survived`), `drone.total_energy_consumed_wh`, `drone.total_distance_km`, and `drone.total_flight_time_min` still add the **full** demanded leg energy (`outbound_wh` / `return_wh`), full `dist_km`, and full `leg_time_min` rather than clamping to the physical energy remaining in the battery prior to depletion (`remaining_energy_wh`).
   - *Verified concrete example:* On Seed `202` (`Standard_Default`, `Extreme Heatwave`, FCFS), `DRONE-04` starts at `180.0 Wh`, never recharges, reaches `LOC-ANGARIA` with `39.39 Wh` (`21.9%` SoC), and crashes on the `41.36 Wh` return leg—recording `181.97 Wh` total consumed energy on a `180.0 Wh` battery and giving FCFS (`24` completed round-trips + `1` return crash) the exact same `1114.67 Wh` fleet energy and `109.32 km` distance as BAPA (`25` completed round-trips). This does **not** affect delivery success, mission success, return-leg failures, or reserve violation counts, which are all 100% accurate.
7. **Latent JavaScript Falsy-Zero Bug in 2D Radar (`src/radar_view.py:204-215`):**
   - Line 204 writes `this.soc = currentEvent.soc || 1.0;` and lines 205–215 do not handle `MISSION_FAILED` or `RETURN_FAILED`. In JavaScript, `0.0 || 1.0` evaluates to `1.0` (`100%`). Because `app.py:127` exclusively runs `BatteryAwareDispatcher()` for the radar tab (which never fails or hits `0.0` SoC), this bug never triggers in current dashboard usage, but would display `100%` SoC if `FCFSDispatcher` failure logs were passed to the radar.
8. **Minor Dashboard UX Details (`app.py`, `src/map_view.py`, `src/radar_view.py`):**
   - `app.py:341, 347-353`: Tab 4 (`Discrete-Event Logs`) remains empty until the user clicks Run on Tab 3, and only displays/exports `sim_bapa` event logs (without labeling that they are BAPA-only or offering a toggle to view `sim_fcfs` failure logs).
   - `src/map_view.py:67`: Depot popup displays static `depot_info['charging_bays']` (`2 slots` from JSON) rather than the active sidebar `charging_bays` slider value; `src/radar_view.py:400-403` similarly draws 2 static dock dots.
   - `app.py:65` (sidebar drone icon URL) and `src/map_view.py:40-60` (OSM/Esri/OpenTopoMap tiles) require live internet access in the browser during presentation.

---

## 5. Report and Experiment Accuracy Assessment

### `PROJECT_REPORT.md` Review
- **Equation-to-Code Fidelity:** **100% Verified Match.** All equations in Section 9 (Haversine distance in `src/network.py`, Poisson inter-arrival times in `src/generator.py`, flight leg duration, `climate_multiplier` with `28.0°C` threshold and `round(..., 3)` in `src/config.py`, linear payload power `210 + 45*m` and leg Wh in `src/models.py`, charger duration `E_needed / (300 * 0.90) * 60` in `src/simulation.py`, and summary metrics in `get_summary_metrics()`) match the executable Python code exactly.
- **Dimensional & Unit Consistency:** **Verified Accurate** across all formulas, prose, and table headers (`km`, `m/s`, `s`, `min`, `hr`, `W`, `W/kg`, `kg`, `Wh`, `°C`, `%`).
- **Node Distance & Telemetry Table (Section 5):** **100% Verified Match** for all 10 delivery nodes (`0.204 km` / `1.28 min` at `LOC-PSTU-MED` through `5.336 km` / `8.41 min` at `LOC-ANGARIA`).
- **Synthetic vs. Real Data Distinction:** **Exemplary.** Sections 4, 5, and 10.3 explicitly distinguish real PSTU/Dumki landmark coordinates from synthetic Poisson orders and hardware parameters, and clearly explain why satellite Land Surface Temperature (LST) is **not** used as ambient air or LiPo cell temperature.
- **Limitations & References:** Limitations in Section 15 are candid and technically accurate (direct corridors without obstacle avoidance, non-expiring `urgency_deadline_min`, scalar symmetric wind penalty, linear battery/charging curves, and eased canvas radar movement). All 6 references in Section 17 (SimPy docs, Hagberg et al. 2008 for NetworkX, Sinnott 1984 for Haversine, Dorling et al. 2017 IEEE TSMC for linear multi-rotor payload power, Law 2015 for DES, and Streamlit/Folium/Plotly docs) are genuine, verifiable, and directly relevant.
- **Unsupported Claims Check:** Zero fabricated results or hardware claims exist; the only residual overstatement is the legacy phrase `"Urban Heat Monitoring"` in the report/presentation subtitle (`PROJECT_REPORT.md:3, 12`, `PRESENTATION_OUTLINE.md:13`).

### Experiment CSVs & `results/EXPERIMENTAL_ANALYSIS.md` Review
- **Paired Fairness:** Verified in `results/run_benchmark_experiments.py:85-103` that for each `(regime, weather, seed)` tuple, one `base_requests` list is generated and deep-copied (`copy.deepcopy(base_requests)`) to both `FCFSDispatcher` and `BatteryAwareDispatcher` with identical fleet, charger, and physics settings.
- **Documented Seeds:** Fixed seeds `[42, 101, 202, 303, 404]` ($n = 5$) are explicitly documented and reproducible.
- **Aggregation & Report Table Accuracy:** Re-running `run_all_experiments()` in memory matched `results/benchmark_per_seed.csv` (`60` rows) and `results/benchmark_aggregated.csv` (`12` rows, sample mean and `ddof=1` sample SD rounded to 2 decimal places) with **zero discrepancies** (`pd.testing.assert_frame_equal` passed). Every value in `PROJECT_REPORT.md` Tables 13.1, 13.2A, 13.2B, Abstract, and Section 14 (`63.52 Wh`, `41.36 Wh`, `104.88 Wh`, `+32.55%` energy scaling) matches the CSV outputs accurately.

---

## 6. Presentation Readiness Assessment

### `PRESENTATION_OUTLINE.md`
- **Structure & Pacing:** Well-paced 12-slide structure suitable for a 10–15 minute undergraduate CSE defense plus live demo.
- **Technical Accuracy:** Accurately explains the study area (`DEPOT-PSTU` + 10 nodes), 4-layer software architecture, SimPy DES processes, immediate concurrency lock, battery/climate equations, FCFS vs. BAPA best-fit logic, 5-seed experimental results, and modeling limitations.
- **Clarity for CSE Undergraduates:** Bullet points and speaker notes use clear, intuitive engineering language without unnecessary jargon.
- **Pre-Presentation Edits Needed:** Replace `[Student Name | ID]`, `[CSE-3XX]`, and `[Supervisor Name & Designation]` on Slide 1, and remove `"Urban Heat Monitoring and"` from the Slide 1 subtitle so examiners do not ask to see an urban heat monitoring module. Ensure active internet access if demonstrating Tab 2's live Folium map tiles.

### `VIVA_PREP.md`
- **Coverage & Accuracy:** Contains 32 high-probability viva questions across 7 sections (DES paradigm, Haversine/NetworkX routing, Poisson arrivals & concurrency lock, battery/weather physics & LST vs. ambient air distinction, FCFS vs. BAPA & 20% safety reserve, charging queues, and delivery vs. mission success results).
- **Student Usability:** Answers are concise, accurate to the actual codebase, and directly prepare an undergraduate student to defend both what the system does and what its intentional simplifications are (e.g., Q8 on direct corridors vs. Dijkstra obstacle routing, Q16 on LST vs. ambient temperature, Q26–Q27 on return-leg crashes).

---

## 7. Critical Issues That Must Be Fixed Before Submission

These items are small, low-risk edits (`0` changes to simulation physics or benchmark logic required), but **should be fixed before packaging/submitting**:

1. **Add Missing `folium` and `streamlit-folium` (and `pytest`) to `requirements.txt`:**
   - Without `folium` and `streamlit-folium` in `requirements.txt`, `python -m streamlit run app.py` fails immediately with `ModuleNotFoundError` in any fresh Python virtual environment.
2. **Fill Title-Page & Slide Metadata Placeholders:**
   - Replace `[CSE-3XX / Enter Course Code]`, `[Enter Student Name]`, `[Enter Student ID / Registration Number]`, `[Level-3, Semester-X / Academic Year]`, and `[Enter Supervisor Name, Designation]` in `PROJECT_REPORT.md` (`lines 14-21`) and `PRESENTATION_OUTLINE.md` (`lines 15-16`).
3. **Remove Legacy `"Urban Heat Monitoring and"` from Report & Slide Subtitles + Fix `README.md` Depot Name:**
   - Update `PROJECT_REPORT.md` (`lines 3, 12`) and `PRESENTATION_OUTLINE.md` (`line 13`) subtitle to match `README.md:3` (*"An Integrated Simulation Framework for Battery-Aware Multi-Drone Delivery Optimization..."*).
   - Update `README.md` (`line 17` and `lines 37-45`) so it correctly identifies `PSTU Central Drone Command & Charging Hub (DEPOT-PSTU)` instead of `Dumki Upazila Health Complex`, and lists the current Phase 7.2 files (`map_view.py`, `radar_view.py`, `tests/`, `results/`, `PROJECT_REPORT.md`, `VIVA_PREP.md`, `PRESENTATION_OUTLINE.md`).

---

## 8. Optional Improvements That Can Wait

These items do **not** block submission and can safely wait (or remain documented as future work):

1. **Clamp Crash-Leg Energy/Distance/Time Telemetry (`src/simulation.py:134-136, 174-176`):** Cap accumulated `total_energy_consumed_wh` on a failed leg at the drone's actual pre-leg `remaining_energy_wh` (and scale partial distance/flight time before crash) rather than adding full demanded leg Wh, or add a one-sentence note in `PROJECT_REPORT.md` Section 15 noting leg-boundary failure accounting. *(Note: changing `simulation.py` would require re-running `results/run_benchmark_experiments.py` to keep CSVs in sync.)*
2. **Tab 4 Event Log Policy Selector (`app.py:340-353`):** Allow selecting between `BAPA` and `FCFS` event logs in Tab 4 (and clarify the active policy in the subheader) so users can inspect `RETURN_FAILED` events directly in the UI.
3. **2D Radar Nullish Coalescing & Failure State (`src/radar_view.py:204-215`):** Replace `currentEvent.soc || 1.0` with `currentEvent.soc ?? 1.0` and handle `MISSION_FAILED` / `RETURN_FAILED` states in case non-BAPA logs are ever visualized on the radar.
4. **Dynamic Charger Count in Map Popup (`src/map_view.py:67`) & Minor Typos (`src/__init__.py:1`, `VIVA_PREP.md:145, 180`):** Pass `charging_bays` to `build_dumki_folium_map()`, update `src/__init__.py` docstring, fix `.Occupying` spacing in `VIVA_PREP.md:145`, and clarify `"7 test modules + conftest.py"` in `VIVA_PREP.md:180`.
5. **Future Research Extensions (Already Documented in Report Section 15):** Pending order deadline expiration (`urgency_deadline_min`), multi-hop obstacle-avoidance routing in NetworkX, directional 2D wind vectors, and CC-CV non-linear charging curves.

---

## 9. Final Recommendation

### **VERDICT: `READY WITH MINOR FIXES`**

**Justification:**  
The core Discrete-Event Simulation engine (`SimPy`), concurrency locking, delivery-vs.-mission failure accounting, `FCFS` and `BAPA` dispatchers, spatial Haversine network, Streamlit visualization builders, `29/29` automated `pytest` tests, `60`-run multi-seed CSV benchmark suite, mathematical report, presentation outline, and viva guide are **genuinely implemented, reproducible, and mathematically consistent**. Resolving the three minor non-engine items in **Section 7** (`requirements.txt` missing `folium`/`streamlit-folium`, student/course metadata placeholders, and the legacy subtitle / `README.md` depot text) will take under 10 minutes and make the project **100% ready for final academic submission and live viva defense**.

