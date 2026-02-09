import cv2
import numpy as np

def draw_cyberpunk_detections(image_bytes: bytes, detections: dict):
    """
        Draw Bounging-Box with CyberPunk/HUD style over the incoming picture
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Unable to Decode imanges")
    
    boxes = detections.get("boxes", [])
    class_ids = detections.get("class_ids", [])
    confidences = detections.get("confidences", [])
    
    # Color Pallette 
    COLOR_HEALTHY = (57, 255, 20)
    COLOR_DAMAGED = (147, 20, 255)
    COLOR_GREEN =  ( 0,225,125)
    COLOR_BG = (0, 0, 0)
    
    for idx, (box, class_id) in enumerate(zip(boxes, class_ids)):
        x, y, w, h = box
        
        # Validate >Coordinates 
        if w <= 0 or h <= 0:
            continue
        
        # Class Setting
        if class_id == 0:
            
            color = COLOR_HEALTHY
            label = "SYS: HEALTHY"
            
        elif class_id == 1 :
            
            color = COLOR_DAMAGED
            label = "SYS: CRITICAL"
            
        elif class_id == 2 :
            
            color = COLOR_GREEN
            label = "SYS: GREEN"
            
        else :  
            
            continue
        
        # Add Confident to the label Reactangle 
        
        if idx < len(confidences):
            
            label += f" {confidences[idx]:.2f}"

        # Main Box 
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)

        # Reinforce Tag
        line_len = int(min(w, h) * 0.2)
        thickness = 3
        
        # Upper Left Tag
        cv2.line(img, (x, y), (x + line_len, y), color, thickness)
        cv2.line(img, (x, y), (x, y + line_len), color, thickness)
        
        # Upper Right Tag
        cv2.line(img, (x + w, y), (x + w - line_len, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + line_len), color, thickness)
        
        # Bottom Left Tag
        cv2.line(img, (x, y + h), (x + line_len, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - line_len), color, thickness)
        
        # Bottom R>ight Tag
        cv2.line(img, (x + w, y + h), (x + w - line_len, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - line_len), color, thickness)

        # Best Size tag
        font_scale = 0.6
        font_thickness = 2
        
        (text_w, text_h), baseline = cv2.getTextSize(
            label, 
            cv2.FONT_HERSHEY_SIMPLEX, 
            font_scale, 
            font_thickness
        )
        
        label_y = max(y - 10, text_h + 10)
        
        # Black BackGround 
        cv2.rectangle(
            img, 
            (x, label_y - text_h - 8), 
            (x + text_w + 8, label_y + 2), 
            COLOR_BG, 
            -1
        )
        
        # Inner Text
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

    # Code within Best Quality 
    
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
    success, buffer = cv2.imencode(".jpg", img, encode_param)
    
    if not success:
        
        raise ValueError("Unable to encode the processed Imanges!")
    
    return buffer.tobytes()