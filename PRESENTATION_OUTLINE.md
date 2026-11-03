# PRESENTATION SLIDE OUTLINE (12 SLIDES)

**Project:** Climate-Aware Intelligent Urban Drone Network  
**Course:** Simulation and Modeling  
**Recommended Presentation Duration:** 10–15 Minutes + Live Demo & Q&A

---

## Slide 1: Project Title & Student Details

- **Slide Title:** Climate-Aware Intelligent Urban Drone Network: Battery-Aware Multi-Drone Delivery Simulation for Dumki, Patuakhali
- **Bullet Points:**
  - **Subtitle:** An Integrated Simulation Framework for Urban Heat Monitoring and Battery-Aware Multi-Drone Delivery Optimization
  - **Case Study Hub:** Patuakhali Science and Technology University (`DEPOT-PSTU`) & Dumki Upazila
  - **Course:** Simulation and Modeling (`[CSE-3XX]`) — Department of CSE, PSTU
  - **Presented By:** `[Student Name | ID]` | **Supervised By:** `[Supervisor Name & Designation]`
- **Recommended Visual:** Title banner featuring a screenshot of the Streamlit dashboard header and the PSTU/Dumki satellite map view.
- **Speaker Note:** "Assalamu Alaikum and good morning. Today I am presenting our Simulation and Modeling course project—a discrete-event simulation framework that models battery-aware multi-drone emergency and campus delivery from PSTU Main Campus across Dumki Upazila under coastal weather constraints."

---

## Slide 2: Problem Statement & Motivation

- **Slide Title:** Operational Challenges in Rural & Campus Drone Logistics
- **Bullet Points:**
  - Road links between PSTU Campus and rural clinics in Dumki (Angaria, Pangashia, Muradia, Lebukhali) can delay urgent medical deliveries.
  - Multi-rotor UAVs offer rapid aerial delivery ($0.20\text{--}5.34\text{ km}$), but LiPo batteries drain rapidly under cargo weight, summer heatwaves, and coastal winds.
  - **Myopic Dispatch Risk:** Assigning orders naively by arrival order (FCFS) ignores whether a partially used drone can survive the return journey.
  - **Depot Bottleneck:** Multiple returning drones contend for limited charging bays ($c < N$), creating coupled dispatch and recharge queues.
- **Recommended Visual:** Side-by-side conceptual diagram showing (Left) an FCFS drone delivering cargo at Angaria and depleting its battery on the return leg vs. (Right) charging bay queue contention at `DEPOT-PSTU`.
- **Speaker Note:** "While drones bypass rural road delays, their battery endurance drops sharply when carrying heavy packages in $39^\circ\text{C}$ coastal heat and headwinds. If a dispatcher ignores return-leg energy, a drone may drop off its package and crash on the flight home—permanently shrinking the fleet."

---

## Slide 3: Project Objectives & Scope

- **Slide Title:** Objectives, Modeling Boundaries & Academic Honesty
- **Bullet Points:**
  - Build a pure software **Discrete-Event Simulation (DES)** in Python & SimPy (`env.now` event calendar, zero physical hardware claims).
  - Ground spatial distances in **real PSTU & Dumki GPS coordinates** while using reproducible **synthetic Poisson demand streams**.
  - Formulate payload-dependent power draw ($P_{\text{base}} + \alpha m$), ambient weather penalties ($\kappa_{\text{climate}}$), and $M/G/c$ depot charging queues.
  - Propose **BAPA (Battery-Aware & Payload-Constrained Assignment)** and benchmark it fairly against **FCFS** across multiple random seeds.
  - Separate **Customer Delivery Success** from **Round-Trip Mission Success** and verify correctness with 29 automated `pytest` tests.
- **Recommended Visual:** Two-column scope checklist table ("Implemented & Verified" vs. "Explicitly Synthetic / Out-of-Scope").
- **Speaker Note:** "Our objective is a rigorous software simulation testbed. We use real GPS coordinates for PSTU and Dumki nodes, synthetic seeded Poisson demand for controlled experiments, and strict accounting that distinguishes customer package drop-off from safe drone recovery."

---

## Slide 4: Study Area & Spatial Air Corridor Network

- **Slide Title:** Study Area: PSTU Central Hub & Dumki Upazila Corridors
- **Bullet Points:**
  - **Primary Depot (`DEPOT-PSTU`):** PSTU Central Drone Command & Charging Hub ($22.4648^\circ\text{N}, 90.3835^\circ\text{E}$).
  - **4 Campus Nodes ($0.20\text{--}0.51\text{ km}$):** Medical Center, CSE Faculty, Residential Halls, and Agro-Research Farm.
  - **6 Regional Nodes ($1.32\text{--}5.34\text{ km}$):** Dumki Hospital, Dumki Bazar, Muradia, Lebukhali, Pangashia Clinic, and Angaria Council Post.
  - **Distance Model:** Direct single-hop great-circle air corridors computed via the **Haversine formula** ($R = 6371\text{ km}$) in NetworkX.
- **Recommended Visual:** Screenshot of **Tab 2 (`Interactive Real-World Map`)** showing Esri Satellite / OpenStreetMap tiles with dashed flight corridors radiating from PSTU, paired with the corridor distance summary table.
- **Speaker Note:** "Our network is anchored at PSTU Main Campus with 4 short-range campus nodes under half a kilometer and 6 regional Dumki nodes reaching up to 5.34 km at Angaria. Distances are computed via the spherical Haversine formula along direct air corridors."

---

## Slide 5: System Architecture

- **Slide Title:** Modular Four-Layer Software Architecture
- **Bullet Points:**
  - **Domain & Config Layer (`config.py`, `models.py`, `generator.py`):** `DroneSpecs`, `WeatherScenario`, `Drone`, `Battery`, `DeliveryRequest`, and seeded Poisson request generator.
  - **Topology & Policy Layer (`network.py`, `algorithms.py`):** `DumkiNetwork` graph and pluggable `FCFSDispatcher` vs. `BatteryAwareDispatcher`.
  - **DES Kernel (`simulation.py`):** `DroneDeliverySimulation`, `simpy.Environment`, `simpy.Resource` charging bays, and event trace logger.
  - **Interactive Presentation Layer (`app.py`, `map_view.py`, `radar_view.py`):** Streamlit controls, Folium GIS map, 60 FPS HTML5 radar, and Plotly benchmark charts.
- **Recommended Visual:** The 4-layer Mermaid architecture block diagram from `PROJECT_REPORT.md` (Section 7).
- **Speaker Note:** "We kept strict separation of concerns: the physics models and SimPy engine have zero UI dependencies, allowing the exact same simulation core to power both our automated pytest suite and the interactive Streamlit dashboard."

---

## Slide 6: Discrete-Event Simulation Methodology

- **Slide Title:** SimPy Process Lifecycle & Concurrency Hardening
- **Bullet Points:**
  - Three cooperative SimPy generator processes: `_order_arrival_process`, `_dispatch_scheduler_process`, and `_drone_mission_process`.
  - **Immediate Dispatch Lock:** Assigned drones transition synchronously to `OUTBOUND_DELIVERY` in the same simulation tick, preventing duplicate assignment under simultaneous arrivals.
  - **Mission Sequence:** `IDLE` $\to$ `OUTBOUND_DELIVERY` $\to$ Drop-Off $\to$ `RETURNING` $\to$ `WAITING_FOR_CHARGER` (if $\text{SoC} < \text{threshold}$) $\to$ `CHARGING` $\to$ `IDLE`.
  - **Charging Contention:** `simpy.Resource(capacity=c)` enforces FIFO docking queues and tracks exact waiting delay $W_q$.
- **Recommended Visual:** Drone state transition diagram (`stateDiagram-v2` from `PROJECT_REPORT.md` Section 8).
- **Speaker Note:** "SimPy advances virtual time from event to event, simulating 8 hours in milliseconds. Every drone follows a strict state machine, including an immediate concurrency lock at dispatch and FIFO resource queuing at the depot charging bays."

---

## Slide 7: Drone, Battery & Climate Physics Model

- **Slide Title:** Mathematical Formulation: Flight Energy, Weather & Recharging
- **Bullet Points:**
  - **Flight Leg Time:** $T_{\text{leg}} = \frac{1000 \cdot d_{\text{km}}}{12.0\text{ m/s}} + 60\text{ s}$ (cruise time + takeoff/landing overhead).
  - **Payload-Induced Power:** $P_{\text{flight}}(m) = 210\text{ W} + 45\text{ W/kg} \cdot m$ (outbound loaded $0.5\text{--}2.5\text{ kg}$; return empty $0\text{ kg}$).
  - **Climate Multiplier:** $\kappa_{\text{climate}} = 1.0 + 0.015 \max(0, T_{\text{ambient}} - 28^\circ\text{C}) + 0.030 v_{\text{headwind}}$ ($1.060\times$ Temperate to $1.405\times$ Extreme Heatwave).
  - **Leg Energy & Recharging:** $E_{\text{leg}} = P_{\text{flight}}(m) \cdot T_{\text{leg, hr}} \cdot \kappa_{\text{climate}}$ against $C_{\text{batt}} = 180\text{ Wh}$; recharging at $300\text{ W} \times 0.90 = 270\text{ W}$.
  - *Note:* Uses ambient air temperature ($T_{\text{ambient}}$), distinct from satellite ground-skin Land Surface Temperature (LST).
- **Recommended Visual:** Equation summary card alongside a bar comparison of a $5\text{ km}$ flight leg: Empty ($27.81\text{ Wh}$) $\to$ Loaded $2.5\text{ kg}$ ($42.70\text{ Wh}$) $\to$ Loaded + Heatwave ($60.00\text{ Wh}$).
- **Speaker Note:** "Our energy equations maintain dimensional consistency in Watt-hours. Carrying a 2.5 kg medical payload increases power draw by 53.6%, and an extreme coastal heatwave adds another 40.5% penalty—making pre-flight round-trip estimation essential."

---

## Slide 8: Dispatching Algorithms — FCFS vs. BAPA

- **Slide Title:** Baseline FCFS vs. Proposed Battery-Aware Dispatcher (BAPA)
- **Bullet Points:**
  - **Baseline (`FCFSDispatcher`):** Assigns the first idle drone at the depot (`available_drones[0]`) without checking round-trip energy or weather.
  - **Proposed (`BAPA` — Step 1: Feasibility):** Pre-computes $E_{\text{trip}} = E_{\text{outbound}}(m_{\text{pkg}}) + E_{\text{return}}(0)$ under current $\kappa_{\text{climate}}$.
  - **Proposed (`BAPA` — Step 2: Safety Reserve):** Enforces $\text{SoC}_{\text{current}} - E_{\text{trip}}/C_{\text{batt}} \ge 0.20$ ($20\%$ untouchable reserve); otherwise holds the order safely at base.
  - **Proposed (`BAPA` — Step 3: Best-Fit Selection):** Picks the feasible drone leaving the **minimum safe surplus**, saving $100\%$-charged drones for long rural missions.
- **Recommended Visual:** Flowchart comparing FCFS decision path vs. BAPA's 3-stage filter (Payload Check $\to$ Round-Trip + $20\%$ Reserve Gate $\to$ Minimum-Surplus Sort).
- **Speaker Note:** "FCFS is blind to destination distance and weather. BAPA not only blocks unsafe launches that would violate the 20% LiPo reserve, but also smartly assigns medium-battery drones to short campus hops so fully charged drones remain ready for Angaria or Pangashia."

---

## Slide 9: Interactive Dashboard Demonstration

- **Slide Title:** Live Simulation Dashboard & Mission Telemetry (`app.py`)
- **Bullet Points:**
  - **Sidebar Controls:** Dynamic sliders for Fleet Size ($2\text{--}8$), Charging Bays ($1\text{--}4$), Order Count, Poisson Arrival Rate, Weather Scenario, and Random Seed.
  - **Tab 1 — 2D Cinema Radar:** 60 FPS HTML5 Canvas playing back real SimPy mission events, battery HUD percentages, and timeline scrubbing.
  - **Tab 2 — Interactive GIS Map:** Switchable Street, Satellite, and Terrain layers with corridor distance/energy popups.
  - **Tabs 3 & 4 — Live Benchmark & Event Trace:** Paired FCFS vs. BAPA execution cards, grouped success charts, drone telemetry, and downloadable CSV logs.
- **Recommended Visual:** Composite screenshot of **Tab 1 (`2D Live Mission Radar`)** and **Tab 3 (`Benchmark Experiment`)** metric cards.
- **Speaker Note:** "Now I will briefly demonstrate the live Streamlit dashboard—showing how changing weather to Extreme Heatwave immediately updates the climate multiplier, drives the 2D radar playback, and runs a live head-to-head SimPy benchmark."

---

## Slide 10: Multi-Seed Experimental Results

- **Slide Title:** Paired Experimental Evaluation ($5$ Seeds $\times$ $3$ Climates $\times$ $2$ Regimes)
- **Bullet Points:**
  - **Zero Losses Under BAPA:** Across all $30$ BAPA runs ($900$ orders), **0 outbound failures, 0 return-leg crashes, and 0 reserve violations** occurred.
  - **Standard Default + Heatwave ($N=4, c=2, \text{threshold}=50\%$):** FCFS achieved $100\%$ customer delivery but suffered return-leg crashes on 2 of 5 seeds (**$98.40\%$ mission success** vs. **$100.00\%$ BAPA**).
  - **High-Load Stress + Heatwave ($N=3, c=2, \lambda=10/\text{hr}, \text{threshold}=35\%$):** FCFS lost drones on **all 5 seeds** ($1.60$ lost drones/run; all 3 lost on Seed 42), dropping mission success to **$90.84\%$** vs. **$97.70\%$ BAPA**.
  - **Turnaround & Queue Impact:** Preserving fleet survival reduced High-Load Heatwave average delivery time from **$30.44\text{ min}$ (FCFS)** to **$19.13\text{ min}$ (BAPA)**.
- **Recommended Visual:** Grouped bar chart and summary comparison table from `results/EXPERIMENTAL_ANALYSIS.md` comparing Delivery Success (%), Mission Success (%), Return Failures, and Avg Delivery Time (min).
- **Speaker Note:** "Our 5-seed benchmark highlights why separating delivery success from mission success matters: under heatwave stress, FCFS drones drop off packages and die on the return trip, collapsing fleet capacity and driving average wait times over 30 minutes—while BAPA loses zero drones."

---

## Slide 11: Limitations & Future Work

- **Slide Title:** Current Modeling Limitations & Future Extensions
- **Bullet Points:**
  - **Direct Air Corridors:** Uses straight-line Haversine edges; multi-hop Dijkstra/$A^*$ routing around no-fly zones or obstacles is future work.
  - **Order Expiration:** Queued orders do not yet expire past `urgency_deadline_min` (e.g., finite $480\text{ min}$ horizon cutoff leaves late orders queued).
  - **Simplified Aerodynamics & Electrochemistry:** Scalar wind penalty (symmetric outbound/return) and linear charging rather than directional wind vectors and CC-CV taper curves.
  - **2D Radar Trajectory:** Canvas icons use smooth visual frame easing between real SimPy event timestamps rather than exact linear leg interpolation.
- **Recommended Visual:** Roadmap diagram mapping Current Simplifications $\to$ Next-Phase Engineering Upgrades (Obstacle Routing, EDF Deadlines, Vector Wind, Partial Opportunity Charging).
- **Speaker Note:** "In keeping with scientific transparency, we document four main simplifications: direct corridors without obstacle avoidance, non-expiring order deadlines, symmetric wind multipliers, and linear charging curves—each providing a clear direction for future research."

---

## Slide 12: Conclusion

- **Slide Title:** Conclusion & Key Takeaways
- **Bullet Points:**
  - Built and verified a modular **SimPy Discrete-Event Simulation** tailored to PSTU Main Campus and 10 Dumki delivery nodes.
  - Hardened dispatch concurrency and separated customer delivery completion from round-trip vehicle recovery (**29/29 `pytest` tests passing**).
  - Demonstrated quantitatively that **climate- and payload-aware round-trip feasibility checking (BAPA)** prevents return-leg fleet attrition under coastal heatwaves while maintaining competitive turnaround times.
  - Ready for interactive classroom exploration and reproducible benchmarking via `python -m streamlit run app.py`.
- **Recommended Visual:** Clean summary scorecard showing `29/29 Tests Passed`, `60 Multi-Seed Runs Verified`, `0 BAPA Drone Losses`, and QR/command box to run the app.
- **Speaker Note:** "To conclude, our simulation proves that accounting for payload mass, ambient heat/wind penalties, and return-leg battery reserves before takeoff is essential for reliable multi-drone medical logistics. Thank you—I welcome your questions."

