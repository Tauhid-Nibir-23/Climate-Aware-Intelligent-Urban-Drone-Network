# VIVA PREPARATION GUIDE — CLIMATE-AWARE INTELLIGENT URBAN DRONE NETWORK

**Course:** Simulation and Modeling  
**Case Study:** PSTU Main Campus (`DEPOT-PSTU`) & Dumki Upazila, Patuakhali  
**Total Questions:** 32 Likely Viva Questions with Clear, Code-Accurate Answers

---

## Section A: Project Purpose & Simulation Paradigm

### Q1. What is the main goal of your project?
**Answer:**  
Our project simulates a multi-drone emergency and campus delivery network based at **PSTU Main Campus (`DEPOT-PSTU`)** serving 10 locations across PSTU and Dumki Upazila. Its main goal is to compare a naive **First-Come, First-Served (FCFS)** dispatch policy against a **Battery-Aware and Payload-Constrained Dispatcher (BAPA)** under realistic battery drain, payload weight, hot/windy weather penalties, and limited charging bays.

### Q2. Why is this a software simulation rather than a physical drone hardware project?
**Answer:**  
This project was built for the **Simulation and Modeling** course. Building and flying multiple autonomous cargo drones across 5 km rural corridors involves high cost, aviation regulations, and crash hazards. A software simulation lets us safely test 8 hours of operations in less than a second, run controlled "what-if" experiments (like an extreme heatwave or losing charging bays), and compare scheduling algorithms reproducibly using fixed random seeds.

### Q3. Why did you choose Discrete-Event Simulation (DES) and SimPy instead of a `while` loop with `time.sleep()`?
**Answer:**  
In a delivery system, state changes happen at specific moments—order arrival, takeoff, package drop-off, depot return, charger acquisition, and charger release. Using **SimPy**, the virtual clock (`env.now`) jumps directly from one event timestamp to the next without wasting CPU cycles on empty seconds or real-time waiting. SimPy also provides `simpy.Resource`, which handles multi-drone FIFO queuing at the charging bays cleanly and accurately.

### Q4. Is the 2D radar animation the simulation engine itself, or just a visualization?
**Answer:**  
The 2D radar (`src/radar_view.py`) is strictly a **visualization** of the completed SimPy run. First, `DroneDeliverySimulation` runs in Python and produces the chronological `events_log`. Then, the HTML5 Canvas reads those real timestamps and State-of-Charge (`SoC`) logs to animate the drones.

---

## Section B: Geography, Network & Routing

### Q5. Which parts of your data are real and which parts are synthetic?
**Answer:**  
- **Real geographic data:** The GPS coordinates and names of the central hub (`DEPOT-PSTU` at $22.4648^\circ\text{N}, 90.3835^\circ\text{E}$) and the 10 delivery locations in PSTU Campus and Dumki Upazila (`data/dumki_nodes.json`), displayed on real OpenStreetMap and Esri Satellite map tiles.  
- **Synthetic data:** Order arrival times, package weights ($0.5\text{--}2.5\text{ kg}$), urgency deadlines, drone hardware parameters, and weather scenario multipliers are synthetic modeling inputs.

### Q6. Why do you use the Haversine formula to compute flight distance?
**Answer:**  
Our nodes are stored as latitude and longitude coordinates in degrees. Simple Euclidean distance on degrees is inaccurate because Earth is spherical and longitude spacing shrinks with latitude. The **Haversine formula** (`src/network.py`) accurately calculates great-circle surface distance in kilometers using Earth radius $R = 6371.0\text{ km}$.

### Q7. What are the shortest and longest delivery routes in your network?
**Answer:**  
From `DEPOT-PSTU`:  
- **Shortest route:** PSTU Campus Medical Center (`LOC-PSTU-MED`) at **$0.204\text{ km}$** ($\approx 1.28\text{ min}$ one-way flight).  
- **Longest route:** Angaria Union Council Post (`LOC-ANGARIA`) at **$5.336\text{ km}$** ($\approx 8.41\text{ min}$ one-way flight).

### Q8. You used NetworkX to build the graph. Did you implement obstacle avoidance or multi-hop Dijkstra routing?
**Answer:**  
No. Currently, `DumkiNetwork` builds a complete graph of direct point-to-point Haversine air corridors and looks up the direct edge distance (`self.graph[origin_id][dest_id]["distance_km"]`) between `DEPOT-PSTU` and the destination. Obstacle avoidance around buildings or no-fly zones using multi-hop Dijkstra or $A^*$ pathfinding is not currently implemented and is noted as future work.

---

## Section C: Order Arrivals & Concurrency

### Q9. How are delivery orders generated in the simulation?
**Answer:**  
Orders are generated in `src/generator.py` using a **homogeneous Poisson arrival process**. The time gap between consecutive orders follows an **exponential distribution** (`rng.expovariate(1.0 / mean_interval_min)`), where `mean_interval_min = 60.0 / arrival_rate_per_hour`. Destinations are chosen uniformly at random among the 10 nodes, and package weights are sampled uniformly between $0.5\text{ kg}$ and $2.5\text{ kg}$.

### Q10. How do you ensure experiments are fair and reproducible?
**Answer:**  
We use an isolated `random.Random(random_seed)` instance so the same seed (e.g., `42`) always generates the exact same order list. When comparing FCFS and BAPA, we pass `copy.deepcopy(base_requests)` to both simulations so both policies face the exact same orders, weights, arrival times, fleet size, charging bays, and weather.

### Q11. What happens if two or more orders arrive at the exact same simulated minute when only one drone is idle?
**Answer:**  
In Phase 7.1, we hardened `_dispatch_scheduler_process` (`src/simulation.py`) with an **immediate concurrency lock**. The moment a drone is selected for the first order, its status is immediately set to `DroneStatus.OUTBOUND_DELIVERY` and `current_request_id` is locked—before SimPy starts the flight generator. When the loop checks the second order in the same tick, `drone.is_available()` returns `False`, so the second order stays safely in `pending_orders` until a drone becomes idle again.

---

## Section D: Drone, Battery & Weather Physics

### Q12. How is flight duration calculated for a delivery leg?
**Answer:**  
Each one-way leg takes cruise time plus a fixed takeoff/landing maneuver overhead:
$$T_{\text{leg, s}} = \frac{1000 \times d_{\text{km}}}{12.0\text{ m/s}} + 60.0\text{ s}$$
We divide by $60$ to get minutes for SimPy timeouts, and divide by $3600$ to get hours for Watt-hour energy calculations.

### Q13. How is battery energy consumption calculated?
**Answer:**  
In `Battery.calculate_trip_energy_wh` (`src/models.py`), power increases linearly with payload mass:
$$P_{\text{flight}}(m) = 210.0\text{ W} + (45.0\text{ W/kg} \times m_{\text{payload}})$$
Then electrical energy in Watt-hours ($\text{Wh}$) is:
$$E_{\text{leg}} = P_{\text{flight}}(m) \times T_{\text{leg, hr}} \times \kappa_{\text{climate}}$$
On the outbound leg, $m_{\text{payload}}$ is the package weight ($0.5\text{--}2.5\text{ kg}$). On the return leg, the package has been dropped off, so $m_{\text{payload}} = 0.0\text{ kg}$ ($P_{\text{flight}} = 210.0\text{ W}$).

### Q14. Why does the return flight consume less energy than the outbound flight?
**Answer:**  
Because the drone drops off the package at the destination node. Flying back empty ($0\text{ kg}$ payload) uses only the base hover/cruise power of $210\text{ W}$, whereas carrying a $2.5\text{ kg}$ package outbound uses $210 + 45 \times 2.5 = 322.5\text{ W}$ ($53.6\%$ higher power draw).

### Q15. What do the climate/weather factors represent in `src/config.py`?
**Answer:**  
`WeatherScenario.climate_multiplier` models the extra electrical power needed in hot and windy coastal weather:
$$\kappa_{\text{climate}} = 1.0 + 0.015 \cdot \max(0,\; T_{\text{ambient}} - 28^\circ\text{C}) + 0.030 \cdot v_{\text{headwind}}$$
High air temperature reduces air density (requiring faster rotor spin for lift) and increases battery internal resistance, while headwinds increase aerodynamic drag. The three scenarios give $1.060\times$ (Temperate), $1.180\times$ (Moderate Summer), and $1.405\times$ (Extreme Heatwave).

### Q16. Is satellite Land Surface Temperature (LST) the same as ambient air or battery temperature?
**Answer:**  
No—and this is an important physical distinction. Satellite thermal sensors measure **Land Surface Temperature (LST)** (the hot surface of roofs, roads, or soil), which is often much higher than the **ambient air temperature** ($T_{\text{ambient}}$) at drone flying altitude, and also different from internal **battery cell temperature**. Our simulation uses ambient air temperature ($26^\circ\text{C}\text{--}39^\circ\text{C}$) and wind speed, not raw satellite LST.

### Q17. What are the battery units, and how do you prevent invalid battery states?
**Answer:**  
Battery capacity is $180.0\text{ Wh}$, and State-of-Charge (`current_soc`) is stored as a fraction between $0.0$ ($0\%$) and $1.0$ ($100\%$). `Battery` validates inputs so negative discharge/recharge energy, negative distance, or negative payload raises a `ValueError`, and `current_soc` is clamped strictly to $[0.0, 1.0]$.

---

## Section E: Dispatching Algorithms (FCFS vs. BAPA)

### Q18. How does the Baseline FCFS algorithm work?
**Answer:**  
`FCFSDispatcher` (`src/algorithms.py`) looks at all drones that are `IDLE` at `DEPOT-PSTU` with `current_soc > 0` and within the $2.5\text{ kg}$ payload limit, and simply picks the first one in the list (`available_drones[0]`). It **never** checks whether that drone has enough battery for the distance or weather.

### Q19. Why is FCFS called "FCFS + Greedy" if it doesn't compute nearest drone distance?
**Answer:**  
Because all idle drones wait at the same central depot (`DEPOT-PSTU`), every idle drone is at the exact same distance from the customer. Thus, picking `available_drones[0]` is an index-greedy selection of the first idle drone at the hub rather than a spatial nearest-neighbor search across multiple depots.

### Q20. How does your proposed BAPA algorithm work?
**Answer:**  
`BatteryAwareDispatcher` (BAPA) performs three steps before assigning any order:
1. Calculates the exact **round-trip energy** ($E_{\text{outbound}}(m_{\text{pkg}}) + E_{\text{return}}(0)$) under the current weather multiplier.
2. Checks the **safety reserve constraint**: projected final battery after returning to depot must be at least $20\%$ ($\text{SoC}_{\text{proj}} \ge 0.20$).
3. Among all safe drones, picks the **best-fit drone**—the one leaving the smallest safe surplus above $20\%$—so $100\%$-charged drones are saved for long rural trips like Angaria or Pangashia.

### Q21. What does the 20% battery safety reserve (`min_reserve_soc = 0.20`) mean in practice?
**Answer:**  
It means $36.0\text{ Wh}$ ($20\%$ of $180.0\text{ Wh}$) is treated as an untouchable emergency buffer. In real LiPo batteries, discharging below $20\%$ causes severe voltage sag, permanent cell degradation, and leaves zero margin for unexpected wind gusts. BAPA refuses to launch a mission if the drone would return with less than $20\%$ $\text{SoC}$.

### Q22. What happens under BAPA if no currently idle drone has enough battery for a long-distance order?
**Answer:**  
`select_drone_for_request()` returns `None`. The long-distance order stays safely in `pending_orders` and is re-checked every simulated minute until a recharged drone becomes `IDLE`. Meanwhile, if a shorter campus order is behind it in `pending_orders`, an available medium-battery drone can still serve that shorter order.

---

## Section F: Charging Station & Queuing Theory

### Q23. How do charging queues work at the PSTU depot?
**Answer:**  
The charging station is modeled as `simpy.Resource(self.env, capacity=num_charging_bays)` (default $c = 2$ bays). When a drone returns to the depot with `current_soc < recharge_threshold_soc` (default $0.50$), it enters `WAITING_FOR_CHARGER` and yields a resource request. If all $c$ bays are busy, SimPy automatically places the drone in a FIFO queue and records the exact waiting time `wait_duration = env.now - wait_start` until a bay opens.

### Q24. How is recharging time calculated once a drone gets a charging bay?
**Answer:**  
First we compute missing energy: $E_{\text{needed}} = 180.0 \times (1.0 - \text{SoC})$. Then we divide by effective charger power ($300\text{ W} \times 0.90\text{ efficiency} = 270\text{ W}$) and multiply by $60$ to get minutes:
$$T_{\text{charge, min}} = \frac{180.0 \times (1.0 - \text{SoC})}{300.0 \times 0.90} \times 60$$
For example, recharging from $50\%$ to $100\%$ ($90\text{ Wh}$) takes exactly $20.0\text{ minutes}$.

### Q25. Why doesn't a drone recharge after every single trip?
**Answer:**  
If a drone flies a short $0.22\text{ km}$ mission to PSTU CSE Faculty, it uses less than $5\%$ battery and returns at $\sim 95\%$ $\text{SoC}$.Occupying a charging bay at $95\%$ would unnecessarily block other low-battery drones. Therefore, drones only queue for charging when returning below `recharge_threshold_soc` (default $50\%$).

---

## Section G: Metrics, Results & Limitations

### Q26. What is the difference between "Delivery Success" and "Mission Success" in your project?
**Answer:**  
- **Delivery Success (`completed_orders`):** The customer received the package at the destination node (`PACKAGE_DELIVERED`).  
- **Mission Success (`completed_missions`):** The drone delivered the package **and** flew all the way back to `DEPOT-PSTU` safely without running out of battery (`RETURNED_TO_DEPOT`).  
If a drone delivers its package at Angaria and then runs out of battery on the way home (`RETURN_FAILED`), Delivery Success is $1$, Failed Delivery is $0$ (no double-counting!), Return-Leg Failure is $1$, and Mission Success is $0$.

### Q27. Why did FCFS mostly fail on the *return leg* rather than the *outbound leg* in your experiments?
**Answer:**  
Even on the longest $5.34\text{ km}$ trip with a $2.5\text{ kg}$ load in an Extreme Heatwave, the outbound flight uses $\sim 35.3\%$ $\text{SoC}$ and the empty return flight uses $\sim 23.0\%$ $\text{SoC}$ ($\sim 58.3\%$ round-trip). When drones start above the $35\%$ or $50\%$ recharge threshold, they have enough energy to reach the customer ($> 35.3\%$), so they drop off the package—but they run out of the remaining $23.0\%$ needed on the flight back to PSTU!

### Q28. What did your multi-seed experimental results show overall?
**Answer:**  
Across 60 paired runs ($5$ random seeds $\times$ $3$ weather scenarios $\times$ $2$ load regimes):  
1. **BAPA had zero mid-air failures** ($0$ outbound failures, $0$ return-leg crashes, and $0$ reserve violations across all 900 BAPA orders).  
2. Under **Standard Default + Extreme Heatwave**, FCFS suffered return-leg crashes on 2 of 5 seeds ($98.40\%$ mission success vs. $100.00\%$ for BAPA).  
3. Under **High-Load Stress + Extreme Heatwave**, FCFS lost drones on **all 5 seeds** ($1.60$ lost drones out of $3$ on average; all $3$ drones lost on Seed 42), dropping mission success to $90.84\%$ and raising average delivery time to $30.44\text{ min}$ versus $19.13\text{ min}$ for BAPA.

### Q29. How did BAPA sometimes achieve a *lower* average delivery time and charging wait than FCFS?
**Answer:**  
Two reasons:  
1. In mild/moderate regimes, FCFS repeatedly picks `DRONE-01` first, draining it quickly while other drones sit unused, whereas BAPA spreads short campus trips onto partially used drones and reduces charger congestion.  
2. In Extreme Heatwave stress runs, FCFS permanently loses drones to return-leg crashes, leaving only 1 surviving drone to clear the remaining backlog slowly (e.g., $72.90\text{ min}$ average wait on Seed 303), while BAPA keeps all 3 drones alive.

### Q30. How is Drone Fleet Utilization calculated?
**Answer:**  
In `get_summary_metrics()`, fleet flight utilization is total flight minutes summed across all $N$ drones divided by total available fleet capacity minutes ($N \times T_{\text{sim}}$), multiplied by $100\%$.

### Q31. How did you verify that your simulation code is bug-free?
**Answer:**  
We conducted a full code audit (`AUDIT_REPORT.md`), fixed two critical bugs (the same-tick dispatch concurrency lock and return-leg failure accounting), and wrote **29 automated unit and regression tests** across 8 test modules using `pytest` (`test_drone.py`, `test_battery.py`, `test_dispatch.py`, `test_algorithms.py`, `test_charging.py`, `test_simulation.py`, `test_metrics.py`), all passing $100\%$.

### Q32. What are the main limitations of your current simulation, and how would you extend it in the future?
**Answer:**  
- **Current limitations:** Direct Haversine flight paths without obstacle/no-fly-zone avoidance; pending orders do not expire after `urgency_deadline_min`; wind is modeled as a uniform scalar penalty rather than directional headwind/tailwind vectors; linear battery discharge/charging instead of non-linear LiPo CC-CV curves; and eased visual movement on the 2D canvas radar.  
- **Future work:** Add multi-hop Dijkstra/$A^*$ obstacle avoidance, Earliest-Deadline-First (EDF) urgency expiration, directional 2D wind vectors, and partial opportunity charging at the hub.
