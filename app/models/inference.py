import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path


#  Apple Detection Call Model 
class AppleInference:
    
    def __init__(self, model_path: str):
    
        if not Path(model_path).exists():
    
            raise FileNotFoundError(f"No se encontró el modelo en: {model_path}")
            
        self.session = ort.InferenceSession(
            model_path, 
            providers=['CPUExecutionProvider']
        )
        
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        print(f"Input shape: {self.input_shape}")
        self.classes = ["apple", "damaged_apple"]

    def _preprocess(self, img_bgr):
        """Set the image to the model : Resize,  Normalitzation and axis change"""
        img = cv2.resize(img_bgr, (640, 640))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)
        img = np.expand_dims(img, axis=0)
        return img

    def run_inference(self, image_bytes: bytes):
        """Excecute Detection , then it returns the apple number \counting/"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 1. Get Original Dimensions
        orig_h, orig_w = img_original.shape[:2]
        print(f"Imagen original: {orig_w}x{orig_h}")
        
        # 2. Pre-Processing
        input_tensor = self._preprocess(img_original)
        
        # 3. Run the Model. 
        outputs = self.session.run(None, {self.input_name: input_tensor})
        predictions = np.squeeze(outputs[0]).T
        
        # 4. Split boxes , its scores 
        boxes = predictions[:, :4]
        scores = predictions[:, 4:]
        
        print(f"Prediction way: {predictions.shape}") 
        print(f"Max Confident Detected: {np.max(scores):.4f}")
        
        # 5. Confident Filtering
        conf_threshold = 0.35
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)
        mask = confidences > conf_threshold
        print(f"Max Confident Detected : {np.max(confidences):.4f}")
        filtered_confidences = confidences[mask]
        filtered_class_ids = class_ids[mask]
        filtered_boxes = boxes[mask]
        
        print(f"Detection before pulling NMS: {len(filtered_boxes)}")
        
        # 6. Convert into  NMS  suitable format
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
            0.4
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
                label_id = filtered_class_ids[i]
                confidence = filtered_confidences[i]
                
                # get boxes in 640px
                x_640, y_640, w_640, h_640 = nms_boxes[i]
                
                # Back to Original size
                x_real = int(x_640 * x_scale)
                y_real = int(y_640 * y_scale)
                w_real = int(w_640 * x_scale)
                h_real = int(h_640 * y_scale)
                
                # Save only once 
                final_boxes.append([x_real, y_real, w_real, h_real])
                final_class_ids.append(int(label_id))
                final_confidences.append(float(confidence))
                
                # Class Counting in Image  
                
                if label_id == 0:
                    
                    count_red_apple += 1
                    count_healthy_apple += 1
                    
                elif label_id == 1:
                    
                    count_damaged_apple += 1
                    
                elif label_id == 2 :
                    
                    count_green_apple += 1 
                    count_healthy_apple += 1
                    
                else :
                    
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
                "confidences": final_confidences  # ← Nuevo: para mostrar confianza
            }
        }


# Initialize the model engine
model_path = str(Path(__file__).parent / "weights" / "best_model.onnx")
model_engine = AppleInference(model_path)