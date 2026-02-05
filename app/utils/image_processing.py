import cv2
import numpy as np

def draw_cyberpunk_detections(image_bytes: bytes, detections: dict):
    """
    Dibuja bounding boxes con estética Cyberpunk/HUD sobre la imagen.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("No se pudo decodificar la imagen")
    
    boxes = detections.get("boxes", [])
    class_ids = detections.get("class_ids", [])
    confidences = detections.get("confidences", [])
    
    # Paleta de colores
    COLOR_HEALTHY = (57, 255, 20)
    COLOR_DAMAGED = (147, 20, 255)
    COLOR_BG = (0, 0, 0)
    
    for idx, (box, class_id) in enumerate(zip(boxes, class_ids)):
        x, y, w, h = box
        
        # Validar coordenadas
        if w <= 0 or h <= 0:
            continue
        
        # Configuración según clase
        if class_id == 0:
            color = COLOR_HEALTHY
            label = "SYS: HEALTHY"
        else:
            color = COLOR_DAMAGED
            label = "SYS: CRITICAL"
        
        # NUEVO: Agregar confianza al label
        if idx < len(confidences):
            label += f" {confidences[idx]:.2f}"

        # Caja principal
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)

        # Esquinas reforzadas
        line_len = int(min(w, h) * 0.2)
        thickness = 3
        
        # Esquina Superior Izquierda
        cv2.line(img, (x, y), (x + line_len, y), color, thickness)
        cv2.line(img, (x, y), (x, y + line_len), color, thickness)
        
        # Esquina Superior Derecha
        cv2.line(img, (x + w, y), (x + w - line_len, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + line_len), color, thickness)
        
        # Esquina Inferior Izquierda
        cv2.line(img, (x, y + h), (x + line_len, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - line_len), color, thickness)
        
        # Esquina Inferior Derecha
        cv2.line(img, (x + w, y + h), (x + w - line_len, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - line_len), color, thickness)

        # Etiqueta con mejor tamaño
        font_scale = 0.6
        font_thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(
            label, 
            cv2.FONT_HERSHEY_SIMPLEX, 
            font_scale, 
            font_thickness
        )
        
        label_y = max(y - 10, text_h + 10)
        
        # Fondo negro
        cv2.rectangle(
            img, 
            (x, label_y - text_h - 8), 
            (x + text_w + 8, label_y + 2), 
            COLOR_BG, 
            -1
        )
        
        # Texto
        cv2.putText(
            img, 
            label, 
            (x + 4, label_y - 4), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            font_scale, 
            color, 
            font_thickness, 
            cv2.LINE_AA
        )

    # Codificar con mejor calidad
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
    success, buffer = cv2.imencode(".jpg", img, encode_param)
    
    if not success:
        
        raise ValueError("No se pudo codificar la imagen procesada")
    
    return buffer.tobytes()