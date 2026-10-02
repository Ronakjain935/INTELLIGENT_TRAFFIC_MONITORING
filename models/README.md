# YOLO Detection Models

This directory stores YOLO model weights used by the Intelligent Traffic Monitoring System.

## Default Model
The default model specified in `config.yaml` is:
- **`yolov8n.pt`**: YOLOv8 Nano (optimized for real-time CPU & GPU inference).

## Automatic Download
When you first run the application or tests, `ultralytics` will automatically download `yolov8n.pt` (approx. 6.2 MB) if it is not found locally.

## Using Custom Weights
To use a custom trained model (for example a fine-tuned traffic dataset):
1. Place your `.pt` file in this directory (e.g., `models/traffic_yolov8.pt`).
2. Update `config.yaml`:
   ```yaml
   model:
     name: "models/traffic_yolov8.pt"
   ```
