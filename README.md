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
- **Spatial Topology:** Central depot at Dumki Upazila Health Complex serving rural clinics and union council posts.
- **Flight Energy & Payload:** Drone battery depletion non-linearly influenced by package weight ($m_{payload}$) and ambient weather multipliers ($\kappa_{climate}$).
- **Charging Queues ($M/M/c$):** Shared charging bay contention and queuing delays.

---

## ⚡ How to Run

In your project directory terminal, run:

```bash
python -m streamlit run app.py
```

*Note: We recommend using `python -m streamlit run app.py` on Windows to avoid Python Scripts PATH issues.*

---

## 📁 Project Architecture

- `app.py`: Streamlit interactive web dashboard and benchmarking suite.
- `data/dumki_nodes.json`: Verified coordinates for Dumki depot and regional delivery nodes.
- `src/config.py`: Physical drone specs, battery thresholds, and weather scenario multipliers.
- `src/network.py`: Haversine distance calculator and NetworkX spatial graph.
- `src/models.py`: Dataclasses for Drone, Battery, DeliveryRequest, and Status enums.
- `src/generator.py`: Reproducible Poisson order stream generator.
- `src/algorithms.py`: FCFS vs Battery-Aware Dispatcher implementations.
- `src/simulation.py`: SimPy discrete-event simulation engine with charging bay queues.
- `archive_legacy_heat_explorer/`: Archived legacy files from previous project concept.
