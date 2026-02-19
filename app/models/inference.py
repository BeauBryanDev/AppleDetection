import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path

# Apple Detection Call Model 
class AppleInference:
    
    """
    Inference engine for apple detection using exported YOLOv8 ONNX model.

    Handles image preprocessing, model inference, NMS post-processing,
    and color-based classification (red vs green apples) for healthy detections.
    """
    
    def __init__(self, model_path: str):
        
        """
        Initialize the ONNX inference session.

        Args:
            model_path (str): Path to the .onnx model file

        Raises:
            FileNotFoundError: If model file does not exist
        """
        
        if not Path(model_path).exists():
    
            raise FileNotFoundError(f"No se encontró el modelo en: {model_path}")
            
        self.session = ort.InferenceSession(
            # Use CPU provider for broad compatibility in low hardware environments
            model_path, 
            providers=['CPUExecutionProvider']
            
        )
        # Get Input Name and Shape 
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        print(f"Input shape: {self.input_shape}")
        
        self.classes = ["apple", "damaged_apple"]
    # Original training classes (YOLOv8 output)
    def _preprocess(self, img_bgr):
        """Set the image to the model : Resize,  Normalitzation and axis change
           * Preprocess image for YOLOv8 ONNX input *(640x640, BGR → RGB, Normalize, CHW)*

        - Resize to model input size (640x640)
        - Convert BGR → RGB
        - Normalize to [0,1]
        - Transpose to CHW
        - Add batch dimension

        Args:
            img_bgr: Original image in BGR (OpenCV format)

        Returns:
            np.ndarray: Ready input tensor [1, 3, 640, 640]
        """
        img = cv2.resize(img_bgr, (640, 640))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)
        img = np.expand_dims(img, axis=0)
        return img

    def _classify_apple_color(self, roi: np.ndarray) -> int:
        """
        Clasifica si el apple es red (0) o green (2) basado en color dominante en HSV.
        
        Args:
            roi: Región del bounding box (BGR)
        
        Returns:
            0 para red_apple, 2 para green_apple
        """
        # Convert to HSV (better for colors)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Red Color Mask (Hue 0-10 y 170-180, Sat >100, Value >100)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        
        # Green Mask (Hue 40-80, Sat >100, Value >100) - adjusted for green apples
        lower_green = np.array([40, 100, 100])
        upper_green = np.array([80, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        # Count non-zero pixels (covered area)
        red_pixels = cv2.countNonZero(mask_red)
        green_pixels = cv2.countNonZero(mask_green)
        
        total_pixels = roi.shape[0] * roi.shape[1]
        red_ratio = red_pixels / total_pixels
        green_ratio = green_pixels / total_pixels
        
        print(f"Color analysis: Red ratio {red_ratio:.2f}, Green ratio {green_ratio:.2f}")
        
        # Decidir: si green > red y >0.3 (umbral para evitar ruido), green; else red
        if green_ratio > red_ratio and green_ratio > 0.30:
            return 2  # green_apple
        else:
            return 0  # red_apple

    def run_inference(self, image_bytes: bytes, confidence_threshold: float = 0.45):
        """Excecute Detection , then it returns the apple number \counting/
            Run full detection pipeline on image bytes.

            Returns counts and detection details for visualization and yield estimation.

            Args:
                image_bytes: Raw image data (e.g. from FastAPI UploadFile)
                confidence_threshold: Minimum confidence for detections (default: 0.45)

            Returns:
                dict: { ...}

        """
        # Decode Input bytes to OpenCV format
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_original is None:
            raise ValueError("Failed to decode input image")
        
        # 1. Get Original Dimensions
        orig_h, orig_w = img_original.shape[:2]
        print(f"Imagen original: {orig_w}x{orig_h}")
        
        # 2. Pre-Processing
        input_tensor = self._preprocess(img_original)
        
        # 3. Run the Model. 
        outputs = self.session.run(None, {self.input_name: input_tensor})
        predictions = np.squeeze(outputs[0]).T  # CAREFULL [num_detections, 6] (x_center, y_center, w, h, conf_class0, conf_class1) 
        ## Shape: (num_dets, 4 + num_classes)
        
        # 4. Split boxes (cx,cy,w,h) and scores (conf_class0, conf_class1)
        boxes = predictions[:, :4]
        scores = predictions[:, 4:]
        
        print(f"Prediction way: {predictions.shape}")
        print(f"Max Confident Detected: {np.max(scores):.4f}")

        # 5. Confident Filtering
        conf_threshold = confidence_threshold
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)
        mask = confidences > conf_threshold
        print(f"Max Confident Detected : {np.max(confidences):.4f}")
        filtered_confidences = confidences[mask]
        filtered_class_ids = class_ids[mask]
        filtered_boxes = boxes[mask]
        
        print(f"Detection before pulling NMS: {len(filtered_boxes)}")
        
        # 6. Convert into  NMS  suitable format ::(convert cxcywh → xywh)
        nms_boxes = []
        
        for box in filtered_boxes:
            cx, cy, w, h = box
            x = int(cx - (w / 2))
            y = int(cy - (h / 2))
            nms_boxes.append([x, y, int(w), int(h)])
        
        # 7. Run NMS
        indexes = cv2.dnn.NMSBoxes(
            nms_boxes, 
            filtered_confidences.tolist(), 
            conf_threshold, 
            0.45  # NMS  IoU  Threshold
        )
        
        print(f"Detection after NMS: {len(indexes) if len(indexes) > 0 else 0}")
        
        # 8. Process final results ito fit model for apple detection 
        count_red_apple = 0
        count_green_apple = 0
        count_healthy_apple = 0
        count_damaged_apple = 0
        
        
        #Box settings
        final_boxes = []
        final_class_ids = []
        final_confidences = []
        
        # Scale Normalization 
        x_scale = orig_w / 640
        y_scale = orig_h / 640
        
        if len(indexes) > 0:
            for i in indexes.flatten():
                orig_label_id = filtered_class_ids[i]  # Guardamos el original del modelo
                confidence = filtered_confidences[i]
                
                # get boxes in 640px
                x_640, y_640, w_640, h_640 = nms_boxes[i]
                
                # Back to Original size (640x640) - Scaled Boxes
                x_real = int(x_640 * x_scale)
                y_real = int(y_640 * y_scale)
                w_real = int(w_640 * x_scale)
                h_real = int(h_640 * y_scale)
                
                # Clamp to Images bounds (avoid out-of-range)
                x_real = max(0, x_real)
                y_real = max(0, y_real)
                w_real = min(w_real, orig_w - x_real)
                h_real = min(h_real, orig_h - y_real)
                
                if w_real <= 0 or h_real <= 0:
                    continue
                
                # Color classification only for healthy apples (class 0))
                label_id = orig_label_id
                if label_id == 0:
                    # Extract ROI (Region of Interest)
                    roi = img_original[y_real:y_real + h_real, x_real:x_real + w_real]
                    if roi.size == 0:
                        continue  # Empty ROI, skip color classification    
                    
                    # Temporaly Disable Clasificar color
                    #color_class = self._classify_apple_color(roi)
                    #label_id = color_class  # 0=red, 2=green
                
                # Save only once 
                final_boxes.append([x_real, y_real, w_real, h_real])
                final_class_ids.append(int(label_id))
                final_confidences.append(float(confidence))
                
                # Class Counting in Image  
                if label_id == 0:  # red_apple
                    count_red_apple += 1
                    count_healthy_apple += 1
                    
                elif label_id == 1:  # damaged
                    count_damaged_apple += 1
                    
                elif label_id == 2:  # green_apple
                    count_green_apple += 1 
                    count_healthy_apple += 1
                    
                else:
                    continue 
        
        # Apple Detection 
        print(f"Apples Estimation - Healthy: {count_healthy_apple}, Damaged: {count_damaged_apple} ,  Green Apples {count_green_apple}")
        
        return {
            "counts": {
                "red_apple": count_red_apple,
                "green_apple": count_green_apple,
                "healthy":  count_healthy_apple,
                "damaged_apple": count_damaged_apple,
                "total": count_red_apple + count_green_apple + count_damaged_apple
            },
            "detections": {
                "boxes": final_boxes,
                "class_ids": final_class_ids,
                "confidences": final_confidences
            }
        }


# Initialize the model engine
model_path = str(Path(__file__).parent / "weights" / "best_model.onnx")
model_engine = AppleInference(model_path)
