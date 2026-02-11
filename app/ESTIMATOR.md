# 🍎 Apple Yield Estimator

A computer vision application that estimates apple yield from orchard images. Built from scratch using a fine-tuned **YOLOv8s** model trained on a custom apple dataset prepared with **Roboflow**.

![Apple Detection Demo](link-to-your-demo-gif-or-screenshot)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Model Training](#model-training)
  - [Dataset Preparation](#dataset-preparation)
  - [Training Process](#training-process)
- [Installation](#installation)
- [Usage](#usage)
  - [Inference on Images](#inference-on-images)
  - [Inference on Video/Webcam](#inference-on-video-or-webcam)
  - [Batch Processing](#batch-processing)
- [Project Structure](#project-structure)
- [Results](#results)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## 🚀 Overview

The **Apple Yield Estimator** is a practical deep learning solution for agricultural monitoring. It automates the detection and counting of apples in orchard images, helping farmers and agronomists estimate yield with minimal manual effort.

The system is built from the ground up: a YOLOv8s model was fine-tuned using a high-quality, annotated apple dataset exported from Roboflow. The final model is integrated into a user-friendly Python application that can process images, videos, or live camera feeds.

---

## ✨ Features

- **Accurate Apple Detection**: Fine-tuned YOLOv8s model optimized for apple detection.
- **Real-time Counting**: Instantly count visible apples in an image or frame.
- **Video & Webcam Support**: Process video files or live streams for continuous monitoring.
- **Batch Processing**: Analyze multiple images at once and export results as CSV.
- **Visual Output**: Bounding boxes with confidence scores drawn on output images.
- **Modular Codebase**: Easy to extend for other fruits or agricultural detection tasks.

---

## 🛠️ Tech Stack

- **Python 3.9+**
- **Ultralytics YOLOv8** – Object detection framework
- **Roboflow** – Dataset management, annotation, and export
- **OpenCV** – Image/video processing and visualization
- **PyTorch** – Deep learning backend
- **NumPy / Pandas** – Data handling and CSV export
- **Matplotlib** – Result visualization (optional)

---

## 🧠 Model Training

### Dataset Preparation

1. **Data Collection**: Gathered images of apples in various orchard conditions (lighting, occlusion, ripeness).
2. **Annotation**: Used Roboflow's annotation interface to label apples with bounding boxes.
3. **Preprocessing & Augmentation**: Applied resizing (640x640), auto-orientation, and augmentations like saturation, brightness, and flip to improve robustness.
4. **Export**: Dataset exported in YOLOv8 PyTorch format directly from Roboflow.

**Dataset Summary:**
- Total Images: ~X,XXX
- Train/Val/Test Split: 70/20/10
- Classes: 1 (`apple`)
- Export Format: YOLOv8

### Training Process

The model was fine-tuned starting from the pre-trained YOLOv8s COCO weights.

```bash
yolo train model=yolov8s.pt data=apple_dataset.yaml epochs=50 imgsz=640 batch=16

Results
The fine-tuned YOLOv8s model performs reliably under varying conditions:

Metric	Value
Precision	X.XX
Recall	X.XX
mAP@0.5	X.XX
Inference Speed	~XX ms/image (on GPU)
Sample Detection:

https://path/to/example-output.jpg

```

## 🔮 Future Improvements
Occclusion Handling: Improve counting for heavily overlapped apples.

Size Estimation: Incorporate depth or reference objects to estimate fruit size.

Web Dashboard: Deploy as a web application with a React frontend and FastAPI backend.

Mobile Support: Optimize model for on-device inference (CoreML, TFLite).

Multi-class Extension: Detect other fruits or growth stages.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
Roboflow for providing an excellent dataset management and annotation platform.

Ultralytics for the YOLOv8 framework.

The open-source computer vision community for continuous inspiration.

## Built from scratch with passion for agriculture technology. 🌱
