# Climate-Aware Intelligent Urban Drone Network

**An Integrated Simulation Framework for Battery-Aware Multi-Drone Delivery Optimization**  
*Case Study: Dumki Upazila, Patuakhali, Bangladesh*  
*Course: Simulation and Modeling*

---

## 🚁 Project Overview
This project models and simulates an autonomous multi-drone delivery logistics network serving emergency medical needs across Dumki Upazila, Patuakhali, Bangladesh.

The system utilizes a **Spatial-Temporal Discrete-Event Simulation (DES)** approach built with **SimPy** and **NetworkX**, evaluating operational trade-offs between:
1. **Baseline Dispatching (FCFS + Greedy Nearest Drone)**
2. **Proposed Battery-Aware & Payload-Constrained Dispatching (BAPA)**

### Key Modeled Realities:
- **Spatial Topology:** Central hub at **PSTU Central Drone Command & Charging Hub (`DEPOT-PSTU`)** serving 10 campus and regional delivery destinations—including **Dumki Upazila Health Complex (`LOC-DUMKI-HOSP`)**, rural clinics, and union council posts.
- **Flight Energy & Payload:** Drone battery depletion non-linearly influenced by package weight ($m_{payload}$) and ambient weather multipliers ($\kappa_{climate}$).
- **Charging Queues ($M/M/c$):** Shared charging bay contention and queuing delays.

---

## ⚡ How to Run

In your project directory terminal, run:

```bash
python -m streamlit run app.py
```

*Note: We recommend using `python -m streamlit run app.py` on Windows to avoid Python Scripts PATH issues.*

To run the automated test suite (`29` unit and regression tests):

```bash
python -m pytest -v
```

---

## 📁 Project Architecture

- `app.py`: Streamlit interactive web dashboard, 2D mission radar, interactive GIS map, and live benchmarking suite.
- `run_app.py` / `run.bat`: Convenience launchers for Windows and VS Code.
- `requirements.txt`: Python package dependencies for simulation, dashboard, mapping, and testing.
- `data/dumki_nodes.json`: Verified coordinates for `DEPOT-PSTU` (PSTU Central Drone Command & Charging Hub) and 10 campus/regional delivery destinations (including `LOC-DUMKI-HOSP`, Dumki Upazila Health Complex).
- `src/`: Core simulation and visualization package:
  - `src/__init__.py`: Package initialization docstring.
  - `src/config.py`: Physical drone specs, battery thresholds, and weather scenario multipliers.
  - `src/network.py`: Haversine distance calculator and NetworkX spatial graph.
  - `src/models.py`: Dataclasses for Drone, Battery, DeliveryRequest, and Status enums.
  - `src/generator.py`: Reproducible Poisson order stream generator.
  - `src/algorithms.py`: FCFS vs. Battery-Aware Dispatcher (BAPA) implementations.
  - `src/simulation.py`: SimPy discrete-event simulation engine with charging bay queues and summary metrics.
  - `src/map_view.py`: Interactive Folium Leaflet map builder (OpenStreetMap, Esri Satellite, and Topographic layers).
  - `src/radar_view.py`: HTML5 Canvas 2D live mission radar theater builder.
- `tests/`: Automated `pytest` test suite (`conftest.py`, `test_algorithms.py`, `test_battery.py`, `test_charging.py`, `test_dispatch.py`, `test_drone.py`, `test_metrics.py`, `test_simulation.py`).
- `results/`: Multi-seed paired benchmark suite (`run_benchmark_experiments.py`, `benchmark_per_seed.csv`, `benchmark_aggregated.csv`, `EXPERIMENTAL_ANALYSIS.md`).
- `PROJECT_REPORT.md`: Formal university course report with mathematical formulation and experimental analysis.
- `VIVA_PREP.md`: 32 viva defense questions and code-verified answers.
- `PRESENTATION_OUTLINE.md`: 12-slide defense presentation outline with speaker notes.
- `AUDIT_REPORT.md` / `FINAL_REVIEW_REPORT.md`: Technical audit and final read-only review reports.
- `archive_legacy_heat_explorer/`: Archived legacy files from previous project concept.
