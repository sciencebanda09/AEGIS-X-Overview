# AEGIS-X Architecture Overview

## Pipeline Stages & Timing Budget

| Stage | Module | Median | Budget |
|---|---|---|---|
| Sensor read + sync | `lidar_driver.py` + `camera_detector.py` | 1.0 ms | 2 ms |
| Detection + clustering | `LidarClusterer` + `CameraDetector` | 3.0 ms | 4 ms |
| EKF update | `IMMTracker.update()` | 3.5 ms | 4 ms |
| Assignment | Hungarian solver | 5.3 ms | 6 ms |
| Guidance compute | `APNGuidance.compute_apn_aim()` | 1.5 ms | 2 ms |
| Launch gate | `NetLauncher.decide()` | 0.4 ms | 1 ms |
| Serial command | `ArduinoBridge.send_servo()` | 2.0 ms | 2 ms |
| **Total** | | **13.1 ms** | **21 ms** |

Real-time budget: 80 ms (12.5 Hz loop). p99 = 34 ms — well within budget.

---

## Module Responsibilities

### `main_pi.py` — Orchestrator
- Loads `calibration.json`
- Starts sensor threads (`LidarDriver`, `CameraDetector`)
- Runs main 12.5 Hz control loop
- Coordinates EKF → guidance → launch → Arduino

### `lidar_driver.py` — LiDAR Acquisition
- Background thread: reads RPLiDAR A1M8 scans at 10 Hz
- `LidarClusterer`: angular-gap clustering → 3D drone candidates
- Mock mode for PC testing (no hardware required)

### `camera_detector.py` — Vision Detection
- Background thread: reads Pi Camera at 30 fps
- Backend: YOLOv8n (primary) or BlobDetector (fallback)
- Converts pixel bounding boxes to azimuth/elevation angles

### `ekf_tracker.py` — IMM-EKF Tracker
- 4-model parallel Kalman filter (CV / CA / CT / Singer)
- IMM mixing, model probability update, fused output
- Adaptive Markov transition matrix (Dirichlet update every 50 steps)
- Outputs: fused position, velocity, N-step ahead prediction, track quality

### `guidance.py` — APN Guidance
- Iterative intercept point solver (time-to-go convergence)
- Full APN with acceleration feedforward (N=6.5)
- Lead-angle fast mode for low-latency situations
- Converts 3D aim point to pan/tilt servo angles

### `net_launcher.py` — Launch Decision
- 5-gate state machine: IDLE → COMMIT → FIRED → RELOAD
- Gates: track quality, range window, time-to-go window
- Stale guard: aborts if target stops closing
- Reload cooldown: 25 ticks (~2 s) before re-arm

### `arduino_bridge.py` — Serial Bridge
- Thread-safe serial write with lock
- Change threshold suppresses redundant servo writes (<0.5°)
- Mock mode fallback when Arduino not present

---

## Sensor Fusion Strategy

```
LiDAR cluster [x, y, z]  ──┐
                            ├──► BLUE estimator ──► Mahalanobis gate ──► IMMTracker
Camera az/el + depth est  ──┘    (Sage-Melsa)       χ²(2, 0.99)=9.21
```

- BLUE = Best Linear Unbiased Estimator — minimum-variance fusion
- Mahalanobis gate width adapts to tracker confidence (tight when certain, wide when uncertain)
- Depth from camera estimated via `bbox_area` calibrated at known distance

---

## Thread Architecture

```
Main thread (12.5 Hz)
    │
    ├── lidar_queue  ◄── LidarDriver thread (10 Hz, daemon)
    ├── camera_queue ◄── CameraDetector thread (30 Hz, daemon)
    │
    └── ArduinoBridge (synchronous serial writes, locked)
```

Sensor queues use `put_nowait` — frames are dropped under load rather than
blocking the main control loop. Queue depth = 5 for each sensor.
