import cv2
import numpy as np
import onnxruntime as ort
from pathlib import Path

class AppleInference:
    def __init__(self, model_path: str):
        # 1. Cargar el modelo ONNX
        # Verificamos si existe el archivo para evitar errores de ejecución
        if not Path(model_path).exists():
            raise FileNotFoundError(f"No se encontró el modelo en: {model_path}")
            
        # Seleccionamos el proveedor (CPU es estándar para EC2/Portfolio)
        self.session = ort.InferenceSession(
            model_path, 
            providers=['CPUExecutionProvider']
        )
        
        # Obtener información del modelo (input name y shape)
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape  # [1, 3, 640, 640]
        self.classes = ["apple", "damaged_apple"]

    def _preprocess(self, img_bgr):
        """Prepara la imagen para el modelo: Resize, normalización y cambio de ejes."""
        # Redimensionar a 640x640 (lo que definimos en el entrenamiento)
        img = cv2.resize(img_bgr, (640, 640))
        
        # Convertir BGR a RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalizar de [0, 255] a [0.0, 1.0]
        img = img.astype(np.float32) / 255.0
        
        # Cambiar formato de HWC (Height, Width, Channel) a CHW (Channel, Height, Width)
        img = img.transpose(2, 0, 1)
        
        # Añadir la dimensión del batch: [1, 3, 640, 640]
        img = np.expand_dims(img, axis=0)
        return img

    def run_inference(self, image_bytes: bytes):
        """Ejecuta la detección y devuelve el conteo de manzanas."""
        # Convertir bytes a imagen OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Pre-procesar
        input_tensor = self._preprocess(img_original)
        
        # Ejecutar el modelo en ONNX Runtime
        outputs = self.session.run(None, {self.input_name: input_tensor})
        
        # El output de YOLOv8 ONNX es [1, 6, 8400] -> (cx, cy, w, h, score_class1, score_class2)
        predictions = np.squeeze(outputs[0]).T
        
        # 1. Separar cajas de scores
        boxes = predictions[:, :4]      # cx, cy, w, h
        scores = predictions[:, 4:]     # Probabilidades de clase 0 y 1
        
        print(f"Forma de predicciones: {predictions.shape}") 
        print(f"Máxima confianza detectada: {np.max(predictions[:, 4:])}")
        # Filtrar por confianza (ej: 0.4)
        conf_threshold = 0.4
        
        count_healthy = 0
        count_damaged = 0
        
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)
        
        mask = confidences > conf_threshold
        
        # Aplicamos el filtro
        filtered_confidences = confidences[mask]
        filtered_class_ids = class_ids[mask]
        filtered_boxes = boxes[mask]
        
        # OpenCV NMS necesita la esquina superior izquierda (x, y)
        nms_boxes = []
        
        for box in filtered_boxes:
            
            cx, cy, w, h = box
            x = int(cx - (w / 2))
            y = int(cy - (h / 2))
            nms_boxes.append([x, y, int(w), int(h)])
        
        # 2. Ejecutar NMS con el formato correcto
        indices = cv2.dnn.NMSBoxes(
            nms_boxes, 
            filtered_confidences.tolist(), 
            conf_threshold, 
            0.45 # nms_threshold
        )
        
        count_healthy = 0
        count_damaged = 0
        
        if len(indices) > 0:
            # Aseguramos que los índices se manejen correctamente (flatten)
            for i in indices.flatten():
                label_id = filtered_class_ids[i]
                if label_id == 0:
                    count_healthy += 1
                elif label_id == 1:
                    count_damaged += 1
                    
        return {
            "apple": count_healthy,
            "damaged_apple": count_damaged,
            "total": count_healthy + count_damaged
        }


# Initialize the model engine
model_path = str(Path(__file__).parent / "weights" / "best_model.onnx")
model_engine = AppleInference(model_path)