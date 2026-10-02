# AI-Based Intelligent Traffic Monitoring and Violation Detection System

An enterprise-grade, real-time computer vision and traffic analytics application built using **Python**, **YOLOv8**, **ByteTrack**, **OpenCV**, and **Streamlit**.

Designed as a complete, production-style capstone project for **B.Tech / M.Tech AI/ML and Data Science portfolios**.

---

## 1. Project Overview

Modern urban traffic management requires automated, continuous monitoring to mitigate gridlock and enforce road safety regulations. This system transforms passive CCTV video feeds, recorded traffic footage, and live webcams into an intelligent sensor network.

The system performs real-time:
* **Vehicle Detection & Classification:** Identifies passenger cars, motorcycles, commercial trucks, buses, bicycles, and pedestrians.
* **Multi-Object Tracking:** Assigns and persists unique IDs across video frames using ByteTrack.
* **Virtual Tripwire Counting:** Counts crossing vehicles without duplicate tallies.
* **Traffic Density & Congestion Analysis:** Classifies road occupancy (`LOW`, `MEDIUM`, `HIGH`) and estimates traffic congestion heuristics based on vehicle volume and average pixel speed.
* **Direction & Wrong-Way Detection:** Computes trajectory vectors and alerts operators when vehicles travel against authorized traffic flow.
* **Database & Report Generation:** Logs events to a local SQLite database and exports audit reports in **CSV** and **PDF** formats.

---

## 2. System Architecture

```text
               Input Source (CCTV / Upload / Webcam)
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
       Streamlit Dashboard             Automated Reporting
    (Video HUD + KPI Cards +       (CSV & Formal Audit PDF)
       Interactive Plotly)
```

---

## 3. Technology Stack

* **Programming Language:** Python 3.11 / 3.12 / 3.13
* **Deep Learning & Detection:** [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) (`yolov8n.pt` Nano default)
* **Object Tracking:** ByteTrack multi-object tracking with Hungarian linear assignment (`lap`)
* **Computer Vision:** OpenCV (`opencv-python`)
* **Numeric Computing:** NumPy & Pandas
* **Web Dashboard:** Streamlit
* **Interactive Visualizations:** Plotly
* **Audit Document Generation:** ReportLab (PDF Engine)
* **Database:** SQLite3
* **Configuration:** PyYAML

---

## 4. Directory Structure

```text
intelligent-traffic-monitoring/
│
├── app.py                      # Main Streamlit Dashboard Application
├── requirements.txt            # Python dependencies
├── config.yaml                 # System configurations & thresholds
├── pytest.ini                  # Pytest configuration
├── README.md                   # Complete documentation & interview guide
├── .gitignore                  # Git ignore rules
│
├── models/                     # YOLO model weights storage
│   └── README.md
│
├── data/
│   ├── input/                  # Sample traffic videos & user uploads
│   │   └── sample_traffic.mp4
│   ├── output/                 # Processed video output cache
│   └── reports/                # Exported CSV and PDF audit reports
│
├── src/                        # Modular AI and Computer Vision core
│   ├── __init__.py             # Package exports
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
├── dashboard/                  # Dashboard presentation layer
│   ├── __init__.py
│   └── components.py           # Plotly charts, KPI cards & PDF/CSV generators
│
└── tests/                      # Automated unit test suite
    ├── test_detector.py        # Detector & database unit tests
    ├── test_counter.py         # Counting line & crossing unit tests
    └── test_traffic.py         # Density, congestion, & wrong-way tests
```

---

## 5. Installation and Setup

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

> **Note for Windows Users:** The tracking algorithm uses `lap`. If building from source is restricted, install prebuilt wheels with:
> ```bash
> pip install --user lap
> ```

---

## 6. How to Run

Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`.

---

## 7. User Guide & Demonstration Workflow

1. **Select Input Source:**
   * **Sample Video:** Includes a pre-configured sample clip (`data/input/sample_traffic.mp4`).
   * **Upload Video:** Supports `.mp4`, `.avi`, `.mov`, `.mkv`.
   * **Webcam:** Live camera monitoring via camera index `0`.
2. **Tune Detection Parameters (Sidebar):**
   * **Confidence Threshold:** Adjust minimum detection probability (default: `0.40`).
   * **Traffic Flow Direction:** Set authorized highway flow direction (`RIGHT`, `LEFT`, `DOWN`, `UP`).
   * **Frame Skip:** Set to `1` for full processing or `2` for 2x CPU speedup.
3. **Start Monitoring:**
   * Click **`▶ Start`**. The video stream will begin rendering bounding boxes, tracking trails, and the virtual counting line.
4. **Inspect Metrics:**
   * Switch between tabs:
     * **🎥 Live Surveillance:** View the live camera HUD and real-time alerts.
     * **📊 Traffic Analytics:** Inspect vehicle distribution donuts, volume over time, and direction breakdowns.
     * **⚠️ Violations & Alerts:** Audit confirmed wrong-way occurrences.
     * **📑 Audit Reports & Export:** Download one-click **CSV** logs and formal **PDF** audit documents.

---

## 8. Running Automated Unit Tests

Execute the automated test suite with pytest:
```bash
pytest
```
Expected output:
```text
tests/test_counter.py ...                                                [ 27%]
tests/test_detector.py ...                                               [ 54%]
tests/test_traffic.py .....                                              [100%]

============================= 11 passed in ~3.5s ==============================
```

---

## 9. AI/ML Engineering & Interview Explanations

### Detection vs. Tracking
* **Detection (YOLOv8):** Operates on static individual frames without memory. Predicts bounding box coordinates, class IDs, and confidence scores.
* **Tracking (ByteTrack):** Maintains temporal continuity by associating bounding boxes between frame $t$ and frame $t+1$ using a Kalman Filter (predicting next location) and the Hungarian algorithm with IoU distance matrices.

### Virtual Line Counting (Tripwire)
* Unlike naive bounding box thresholding, this system models the vehicle's trajectory as a 2D line segment between centroid positions $(x_{t-1}, y_{t-1})$ and $(x_t, y_t)$.
* An intersection is evaluated using vector cross products (CCW algorithm). Once counted, the `track_id` is registered in `counted_ids` to guarantee **zero duplicate counts**.

### Wrong-Way Detection Algorithm
* Centroid history is tracked over a moving window of recent frames.
* Net displacement vector $(\Delta x, \Delta y)$ is computed.
* To eliminate sensor noise and parking micro-movements, a minimum distance threshold ($\ge 15\text{ px}$) is enforced.
* When the detected direction opposes the designated corridor flow, a confirmation accumulator increments. Once the counter exceeds `confirmation_frames` (default: 5 frames), a safety violation is flagged and committed to the database.

### Heuristic Congestion Estimation
* Highway sensors usually rely on physical loop detectors. In computer vision, congestion is an **estimated heuristic** combining visible density tier (`LOW`, `MEDIUM`, `HIGH`) and mean pixel displacement ($\text{px/frame}$).
* High density + sluggish movement ($< 4\text{ px/frame}$) classifies the section as `CONGESTED`.

---

## 10. Future Enhancements

The modular design allows seamless integration of additional modules:
* Automatic License Plate Recognition (ALPR / ANPR)
* Red-light crossing violation detection with signal state tracking
* Helmet and seatbelt non-compliance detection
* Emergency vehicle prioritization (Ambulance / Fire rescue audio-visual detection)
* Cloud-scale edge streaming via RTSP and Docker containerization
