# AI-Based Intelligent Traffic Monitoring and Violation Detection System
### Enterprise AI Traffic Management & Smart City Traffic Command Center

An enterprise-grade, real-time computer vision and intelligent traffic analytics platform built using **Python**, **YOLOv8**, **ByteTrack**, **OpenCV**, **Plotly**, **SQLite**, and **Streamlit**.

Designed as a modern, high-contrast, professional **AI Traffic Operations Center** suitable for college major project presentations, technical interviews, and real-world deployment demos.

---

## 1. Project Overview

Modern urban traffic management demands automated, continuous video telemetry to eliminate bottlenecks, detect dangerous infractions, and enforce corridor safety rules. The **Intelligent Traffic Monitoring System** transforms passive CCTV video streams, drone footage, and highway cameras into an active, real-time AI command center.

### Core Capabilities:
* **Vehicle Detection & Multi-Class Classification:** Detects and classifies passenger cars, motorcycles, commercial trucks, buses, bicycles, and pedestrians using YOLOv8.
* **Multi-Object Tracking (MOT):** Assigns and maintains persistent vehicle tracking IDs across frames using ByteTrack.
* **Virtual Tripwire Counting:** Computes vector cross-product intersections with virtual counting boundaries to tally crossing volume with strict deduplication.
* **Traffic Density & Congestion Analysis:** Classifies traffic density regimes (`LOW`, `MEDIUM`, `HIGH`) and estimates roadway congestion states.
* **Direction & Wrong-Way Detection:** Analyzes trajectory displacement vectors and instantly flags counter-flow vehicles travelling against designated traffic lanes.
* **Real-Time Video HUD:** Renders bounding boxes, directional trajectory trails, virtual tripwires, telemetry status overlays, and prominent red warning banners.
* **SQLite Relational Persistence:** Commits crossing events, timestamps, vehicle classifications, and periodic statistics snapshots.
* **Audit Documentation & Exports:** Generates one-click **CSV** event datasets and official compliance **PDF audit reports** powered by ReportLab.

---

## 2. System Architecture

```text
               Input Source (CCTV / MP4 Upload / Live Camera)
                                  │
                                  ▼
                      Frame Preprocessing & Resizing
                                  │
                                  ▼
                    YOLOv8 Object Detection Engine
                                  │
                                  ▼
                  ByteTrack Multi-Object Tracker
                                  │
                  ┌───────────────┼───────────────┐
                  │               │               │
                  ▼               ▼               ▼
            Virtual Line     Direction &      Occupancy &
              Counter         Wrong-Way        Congestion
            (Crossing)        Detector          Analyzer
                  │               │               │
                  └───────────────┼───────────────┘
                                  │
                                  ▼
                       SQLite Database Storage
                      (Events & Snapshots Log)
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       Command Center Dashboard           Automated Reporting
     (Video HUD + Telemetry Strips +     (CSV & Formal Audit PDF)
         Interactive Plotly)
```

---

## 3. Technology Stack

* **Programming Language:** Python 3.11 / 3.12 / 3.13
* **Deep Learning Engine:** [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) (`yolov8n.pt`, `yolov8s.pt`, `yolov8m.pt`)
* **Object Tracking:** ByteTrack with Kalman filtering and Hungarian matching
* **Computer Vision:** OpenCV (`opencv-python`)
* **Scientific Computing:** NumPy & Pandas
* **Command Center UI:** Streamlit (Custom Dark Command-Center Theme)
* **Interactive Visualizations:** Plotly Express & Plotly Graph Objects
* **Audit Document Generation:** ReportLab (Vector PDF Generation)
* **Data Storage:** SQLite3 (Local Persistent Relational Database)
* **Configuration:** PyYAML

---

## 4. UI Design System & Color Palette

The interface is engineered around an executive, dark command-center aesthetic:

| Element | Color Hex | Role |
| :--- | :--- | :--- |
| **Primary Background** | `#0B1120` | Core page backdrop |
| **Secondary Background** | `#111827` | Sidebar & navigation panel |
| **Card Background** | `#172033` | Metric cards & container panels |
| **Borders** | `#263247` | Crisp divider lines & card borders |
| **Primary Accent** | `#38BDF8` | System telemetry & primary highlights |
| **Success** | `#22C55E` | Normal flow & compliant status |
| **Warning** | `#F59E0B` | Moderate congestion & caution |
| **Danger** | `#EF4444` | Wrong-way alerts & heavy congestion |
| **Text Primary** | `#F8FAFC` | High-contrast crisp typography |
| **Text Secondary** | `#94A3B8` | Subtle metadata and labels |

---

## 5. UI Screenshots & Command Center Modules

> *(Add screenshots of each command center view here for GitHub presentations)*

### 1. ▣ Dashboard Overview
Executive overview featuring 4 large KPI metric cards (`TOTAL VEHICLES`, `ACTIVE VEHICLES`, `WRONG-WAY ALERTS`, `TRAFFIC DENSITY`), live highway status regime card, vehicle modal split, and dynamic Plotly charts.

### 2. 🎥 Live Monitoring
Full-width surveillance feed with custom video dropzone uploader, live OpenCV annotations, tripwire counting lines, real-time FPS throughput strip, and wrong-way alert banners.

### 3. 📊 Analytics
Interactive historical intelligence dashboard with dynamic filters (time range, vehicle class, event type, direction), vehicle distribution donuts, congestion timelines, and directional bar charts.

### 4. ⚠️ Events & Safety Log
Real-time security and traffic violation monitor with critical wrong-way alert banners, searchable event tables, and categorized tabs (`ALL EVENTS`, `VEHICLE COUNT`, `WRONG-WAY`, `CONGESTION`).

### 5. 📄 Reports & Data Export
Executive traffic compliance summary with instant CSV event log downloads, formal PDF compliance reports, and database purge tools.

### 6. ⚙️ Settings
System configuration interface displaying runtime hyperparameters directly from `config.yaml` with safe persistence controls.

### 7. ℹ️ About
Comprehensive platform documentation, technology stack cards, and pipeline dataflow diagrams.

---

## 6. Directory Structure

```text
intelligent-traffic-monitoring/
│
├── app.py                      # Main Command Center Entry Point & Router
├── requirements.txt            # Python dependencies
├── config.yaml                 # System configurations & thresholds
├── pytest.ini                  # Pytest configuration
├── README.md                   # Complete documentation & project guide
├── .gitignore                  # Git ignore rules
│
├── dashboard/                  # Command Center Presentation Layer
│   ├── __init__.py             # Dashboard package exports
│   ├── styles.py               # Dark command-center CSS design system & tokens
│   ├── header.py               # Top header banner & hardware status chips
│   ├── sidebar.py              # Navigation radio & runtime quick controls
│   ├── components.py           # Reusable KPI cards, status cards & Plotly charts
│   ├── dashboard_page.py       # Overview command center dashboard
│   ├── monitoring_page.py      # Live video surveillance & HUD overlays
│   ├── analytics_page.py       # Historical analytics & dynamic filters
│   ├── events_page.py          # Security violation log & wrong-way alerts
│   ├── reports_page.py         # Automated PDF/CSV audit reports
│   ├── settings_page.py        # Config.yaml inspection and tuning
│   └── about_page.py           # System architecture & technology stack
│
├── src/                        # Modular AI and Computer Vision Core
│   ├── __init__.py             # Source package exports
│   ├── detector.py             # YOLO vehicle detector with thresholding
│   ├── tracker.py              # ByteTrack wrapper & centroid history
│   ├── counter.py              # Virtual counting line & deduplication
│   ├── traffic_analyzer.py     # Density classification & congestion heuristic
│   ├── wrong_way_detector.py   # Vector direction & wrong-way violation engine
│   ├── video_processor.py      # Frame-by-frame pipeline orchestrator & HUD
│   ├── database.py             # SQLite thread-safe event logger
│   ├── statistics.py           # Statistical aggregation & metrics
│   └── utils.py                # Configuration loader, device selector, drawing
│
├── data/
│   ├── input/                  # Sample traffic videos & user uploads
│   ├── output/                 # Processed video output cache
│   ├── reports/                # Exported CSV and PDF audit reports
│   └── traffic_system.db       # Persistent SQLite database
│
└── tests/                      # Automated unit test suite
    ├── test_detector.py        # Detector & database unit tests
    ├── test_counter.py         # Counting line & crossing unit tests
    └── test_traffic.py         # Density, congestion, & wrong-way tests
```

---

## 7. Installation and Setup

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd intelligent-traffic-monitoring
```

### Step 2: Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 8. How to Run

Launch the Command Center application:
```bash
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## 9. User Guide & Demonstration Workflow

1. **Dashboard Overview:**
   * Review all-time cumulative vehicle counts, active vehicles, safety alerts, and road occupancy regimes.
2. **Launch Live Surveillance:**
   * Navigate to **🎥 Live Monitoring**.
   * Select **Preloaded Highway Footage** or upload a video file (`.mp4`, `.avi`, `.mov`).
   * Click **`▶ START AI SURVEILLANCE ANALYSIS`** to initiate YOLO detection, ByteTrack tracking, and live HUD overlays.
3. **Explore Analytics & Filter Data:**
   * Navigate to **📊 Analytics**.
   * Filter records by vehicle classification, flow direction, or event type.
   * Inspect interactive Plotly modal split donuts and traffic surge charts.
4. **Audit Violations:**
   * Navigate to **⚠️ Events** to audit logged wrong-way vehicle infractions.
5. **Generate Compliance Reports:**
   * Navigate to **📄 Reports** and click **`[ 📥 DOWNLOAD CSV REPORT ]`** or **`[ 📄 DOWNLOAD PDF AUDIT ]`**.
6. **Tune Parameters:**
   * Navigate to **⚙️ Settings** to adjust detection thresholds, tripwire positions, or save changes directly to `config.yaml`.

---

## 10. Running Automated Tests

Run the full automated pytest suite:
```bash
pytest
```
Expected output:
```text
tests/test_counter.py ...                                                [ 27%]
tests/test_detector.py ...                                               [ 54%]
tests/test_traffic.py .....                                              [100%]

============================= 11 passed ==============================
```

---

## 11. AI/ML Engineering Core Concepts

### Detection vs. Tracking
* **Detection (YOLOv8):** Operates on static individual frames without temporal continuity. Predicts bounding boxes, class labels, and confidence probabilities.
* **Tracking (ByteTrack):** Maintains persistent IDs across consecutive frames by combining Kalman filter motion prediction with the Hungarian algorithm across high- and low-confidence detection tiers.

### Virtual Line Counting (Tripwire)
* Evaluates trajectory intersections between centroid positions $(x_{t-1}, y_{t-1})$ and $(x_t, y_t)$ and the virtual detection segment.
* Employs 2D vector cross products (CCW orientation test) with immediate ID registration to guarantee **zero duplicate counts**.

### Trajectory Vector Wrong-Way Detection
* Centroid history is tracked over a sliding window.
* A net displacement vector $(\Delta x, \Delta y)$ is evaluated against the configured authorized direction.
* Displacements below a noise threshold ($< 15\text{ px}$) are filtered. Consecutive counter-flow detections trigger a confirmed violation logged to SQLite.

---

## 12. Future Enhancements

* Automatic License Plate Recognition (ALPR / ANPR)
* Red-light crossing violation detection with signal state tracking
* Emergency vehicle acoustic-visual detection and signal preemption
* Cloud-scale edge streaming via RTSP and Docker containerization
