import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path

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
        """Prepara la imagen para el modelo: Resize, normalización y cambio de ejes."""
        img = cv2.resize(img_bgr, (640, 640))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)
        img = np.expand_dims(img, axis=0)
        return img

    def run_inference(self, image_bytes: bytes):
        """Ejecuta la detección y devuelve el conteo de manzanas."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 1. Obtener dimensiones ORIGINALES
        orig_h, orig_w = img_original.shape[:2]
        print(f"Imagen original: {orig_w}x{orig_h}")
        
        # 2. Pre-procesar
        input_tensor = self._preprocess(img_original)
        
        # 3. Ejecutar modelo
        outputs = self.session.run(None, {self.input_name: input_tensor})
        predictions = np.squeeze(outputs[0]).T
        
        # 4. Separar cajas y scores
        boxes = predictions[:, :4]
        scores = predictions[:, 4:]
        
        print(f"Forma de predicciones: {predictions.shape}") 
        print(f"Máxima confianza detectada: {np.max(scores):.4f}")
        
        # 5. Filtrar por confianza
        conf_threshold = 0.45
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)
        mask = confidences > conf_threshold
        print(f"Máximo de confianza detectada: {np.max(confidences):.4f}")
        filtered_confidences = confidences[mask]
        filtered_class_ids = class_ids[mask]
        filtered_boxes = boxes[mask]
        
        print(f"Detecciones antes de NMS: {len(filtered_boxes)}")
        
        # 6. Convertir formato para NMS
        nms_boxes = []
        
        for box in filtered_boxes:
            cx, cy, w, h = box
            x = int(cx - (w / 2))
            y = int(cy - (h / 2))
            nms_boxes.append([x, y, int(w), int(h)])
        
        # 7. Ejecutar NMS
        indexes = cv2.dnn.NMSBoxes(
            nms_boxes, 
            filtered_confidences.tolist(), 
            conf_threshold, 
            0.45
        )
        
        print(f"Detecciones después de NMS: {len(indexes) if len(indexes) > 0 else 0}")
        
        # 8. Procesar resultados finales
        count_healthy = 0
        count_damaged = 0
        final_boxes = []
        final_class_ids = []
        final_confidences = []
        
        x_scale = orig_w / 640
        y_scale = orig_h / 640
        
        if len(indexes) > 0:
            for i in indexes.flatten():
                label_id = filtered_class_ids[i]
                confidence = filtered_confidences[i]
                
                # Obtener caja en 640px
                x_640, y_640, w_640, h_640 = nms_boxes[i]
                
                # Escalar a tamaño original
                x_real = int(x_640 * x_scale)
                y_real = int(y_640 * y_scale)
                w_real = int(w_640 * x_scale)
                h_real = int(h_640 * y_scale)
                
                # ✅ SOLO GUARDAMOS UNA VEZ (aquí estaba el bug)
                final_boxes.append([x_real, y_real, w_real, h_real])
                final_class_ids.append(int(label_id))
                final_confidences.append(float(confidence))
                
                # Contar por clase
                if label_id == 0:
                    count_healthy += 1
                elif label_id == 1:
                    count_damaged += 1
        
        print(f"Conteo final - Healthy: {count_healthy}, Damaged: {count_damaged}")
        
        return {
            "counts": {
                "apple": count_healthy,
                "damaged_apple": count_damaged,
                "total": count_healthy + count_damaged
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