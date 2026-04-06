# AEGIS-X — Autonomous Drone Interception System

> **88.7% success rate · 13 ms median latency · 94.2% track retention**  
> Built on Raspberry Pi 5 + Arduino Mega · Fully edge-native · No cloud dependency

---

AEGIS-X is a real-time autonomous counter-drone system combining multi-model sensor fusion,
predictive tracking, and precision net deployment. The full pipeline — from raw LiDAR/camera
input to launch command — runs in **13 ms median** on a Raspberry Pi 5.

This repository is a **public showcase**: architecture, methodology, benchmarks, and interface
stubs. Core implementations are kept proprietary.  
**For licensing or collaboration → [contact below](#contact--licensing)**

---

## Benchmark Results (v17.0)

Tested over **2,000 simulated frames** · 10 interceptors · 16 max threats · 400 m arena · seed 2025

| Metric | Baseline | v12.0 Fixed | **v17.0** |
|---|---|---|---|
| Success Rate | 83.3% | 77.9% | **88.7%** |
| Breaches | 12 | 17 | **6** |
| Pipeline Median | 21.2 ms | 12.2 ms | **13.1 ms** |
| Pipeline p99 | 50.5 ms | 25.8 ms | **34.0 ms** |
| Track RMSE (median) | — | — | **1.07 m** |
| Max Saturation | 18× | ~12× | **11×** |
| IC Kill Range | 2–13 | 2–7 | **2–8** |
| Avg P_k at fire | 0.108 | 0.133 | **0.188** |

*Full methodology: [`docs/AEGIS_X_Physics_Methodology.pdf`](docs/AEGIS_X_Physics_Methodology.pdf)*

---

## System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      AEGIS-X PIPELINE                      │
│                                                            │
│  [RPLiDAR A1] ──┐                                          │
│                 ├──► [Sensor Fusion]  ──► [IMM-EKF]       │
│  [Pi Camera ×2]─┘    BLUE estimator       4 models        │
│                       Mahal. gate         CV/CA/CT/Singer  │
│                             │                   │          │
│                             └──────┬────────────┘          │
│                                    ▼                       │
│                          [Hungarian Assigner]              │
│                           15-factor cost matrix            │
│                           O(n³), <1 ms at n=16             │
│                                    │                       │
│                                    ▼                       │
│                          [APN Guidance Law]                │
│                           N=6.5, accel feedforward         │
│                                    │                       │
│                                    ▼                       │
│                     [Launch Decision Engine]               │
│                      5-gate quality gating                 │
│                                    │                       │
│                                    ▼                       │
│            [Arduino Bridge] ──► [Net Launcher]             │
│             Serial 115200         Pan/Tilt + Solenoid      │
└────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
aegis-x/
├── README.md
├── LICENSE                                   ← Proprietary
├── requirements.txt
├── docs/
│   └── AEGIS_X_Physics_Methodology.pdf       ← Full physics & math derivations
├── demo/
│   └── benchmark_results.md
├── architecture/
│   └── architecture_overview.md
└── stubs/                                    ← Interface stubs (no implementation)
    ├── simulation/
    │   └── aegis_x_simulation.py             ← Monte Carlo sim engine
    └── hardware/
        ├── pi/
        │   ├── main_pi.py                    ← Pipeline orchestrator
        │   ├── ekf_tracker.py                ← IMM-EKF tracker
        │   ├── guidance.py                   ← APN guidance
        │   ├── net_launcher.py               ← Launch decision engine
        │   ├── lidar_driver.py               ← RPLiDAR acquisition
        │   ├── camera_detector.py            ← YOLO / blob detection
        │   └── arduino_bridge.py             ← Serial command bridge
        └── firmware/
            └── aegis_arduino.ino             ← Arduino Mega (header only)
```

---

## Technical Overview

### Tracking — 4-Model IMM-EKF

Runs four Kalman filters in parallel (CV, CA, CT, Singer), continuously
blending their estimates by measurement likelihood. Handles straight flight,
acceleration, banked turns, and evasive manoeuvres — without manual model
switching. Key implementation choices:

- **Van Loan** exact process-noise discretisation (not σ²·I approximation)
- **Joseph stabilised** covariance update — guaranteed PSD at all timesteps
- **Dirichlet adaptive** Markov transitions — tracker learns threat motion style
- **Mahalanobis chi-squared** gating — gate adapts to tracker confidence

### Guidance — APN (N = 6.5)

Augmented Proportional Navigation with target acceleration feedforward.
Reduces miss distance ~60% vs pure PN against manoeuvring targets.
Iterative intercept solver converges to `|Δtgo| < 1e-4` in ≤10 iterations.

### Assignment — Hungarian Algorithm

Globally optimal interceptor–threat assignment via Kuhn-Munkres.
15-factor cost matrix (geometry, urgency, track quality, IC fatigue,
soft-reassign stability, EC dispatch gates). Solved in O(n³) — `<1 ms`
at n=16 on Pi 5.

### Kill Chain Physics

Full 3-stage kill chain: P_k = P_fuze × P_hit|fuze × P_kill|hit.
Fragment velocity from Gurney equation, lethal density from spatial
fragment model. Subsystem vulnerability by presented area.

---

## Hardware Stack

| Component | Part | Role |
|---|---|---|
| Compute | Raspberry Pi 5 (8 GB) | Main pipeline |
| LiDAR | RPLidar A1M8 | 360° scan, 10 Hz |
| Vision | Pi Camera v3 × 2 | Stereo detection |
| Controller | Arduino Mega 2560 | Servo + solenoid |
| Launcher | Custom net mechanism | Interception |
| Power | 5000 mAh LiPo + regulators | Field deployment |

---

## Pipeline Latency Breakdown

| Stage | Median | p99 | Max |
|---|---|---|---|
| Sensor read + sync | 1.0 ms | 3.6 ms | 4.8 ms |
| IMM-EKF tracker | 3.5 ms | 11.1 ms | 12.5 ms |
| Hungarian assignment | 5.3 ms | 23.4 ms | 24.6 ms |
| Guidance + launch gate | 2.9 ms | 7.3 ms | 8.0 ms |
| **Total pipeline** | **13.1 ms** | **34.0 ms** | **36.5 ms** |

Assignment stage dominates at peak (p99 = 23.4 ms) — expected O(n³) scaling with
active threat count. Total remains within 80 ms real-time budget even at p99.

---

## Physics Models

| Domain | Model | Reference |
|---|---|---|
| Atmosphere | ISA troposphere | ICAO Doc 7488/3 |
| Wind | Dryden turbulence | MIL-HDBK-1797B |
| Weather | Ornstein-Uhlenbeck | Uhlenbeck & Ornstein 1930 |
| Radar | Barton-Skolnik range equation | Skolnik 2001 |
| Sensor fusion | BLUE / Sage-Melsa | Sage & Melsa 1971 |
| Tracking | IMM-EKF | Blom & Bar-Shalom 1988 |
| Process noise | Van Loan discretisation | Van Loan 1978 |
| Covariance | Joseph/Bierman stabilised | Bierman 1977 |
| Assignment | Hungarian (Kuhn-Munkres) | Kuhn 1955 |
| Fragment velocity | Gurney equation | Gurney 1943 |
| Swarm | Reynolds flocking | Reynolds 1987 |
| Evasion | Isaacs optimal | Isaacs 1965 |
| Battery | Peukert discharge | Peukert 1897 |

---

## Applications Beyond Defense

The core engine — real-time multi-agent assignment under uncertainty — generalises to:

| Domain | AEGIS-X analogue |
|---|---|
| Emergency medical | Ambulance dispatch under surge demand |
| Hospital triage | Patient-to-resource assignment with severity weighting |
| Cybersecurity SOC | Alert triage when threat volume exceeds analyst capacity |
| Warehouse robotics | Multi-robot task scheduling with deadline constraints |

---

## License

**Proprietary — All Rights Reserved**

Source code (including stubs) is provided for evaluation and portfolio review only.
Commercial use requires explicit written agreement.  
See [`LICENSE`](LICENSE) for full terms.

---

## Contact & Licensing

**Built by:** [Your Name] · SentrixLab  
**Email:** your@email.com  
**Inquiries:** licensing, defense partnerships, iDEX applications, research collaboration

> *Interested in the full system? Custom deployments and licensing agreements considered.*
