import torch
import numpy as np
from PIL import Image
import cv2
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection, SamModel, SamProcessor

class ZeroShotRulerSegmentationService:
    
    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading Zero-Shot Models on {self.device}...")

        # 1. Load Grounding DINO for text-prompted detection
        dino_id = "IDEA-Research/grounding-dino-tiny"
        self.dino_processor = AutoProcessor.from_pretrained(dino_id)
        self.dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(dino_id).to(self.device)

        # 2. Load Segment Anything Model (SAM) for fine mask generation
        sam_id = "facebook/sam-vit-base"
        self.sam_processor = SamProcessor.from_pretrained(sam_id)
        self.sam_model = SamModel.from_pretrained(sam_id).to(self.device)

    def predict_ruler_mask(self, image_bgr: np.ndarray, text_prompt: str = "a measuring ruler . scale slate .") -> np.ndarray:
        h, w = image_bgr.shape[:2]
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(image_rgb)

        # 1. Detect Ruler Bounding Box via Grounding DINO
        inputs = self.dino_processor(images=pil_img, text=text_prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.dino_model(**inputs)

        results = self.dino_processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=0.25,
            text_threshold=0.20,
            target_sizes=[(h, w)]
        )[0]

        boxes = results["boxes"]
        if len(boxes) == 0:
            print("WARNING: Zero-shot detector found no ruler bounding boxes.")
            return np.zeros((h, w), dtype=np.uint8)

        # Select box with highest confidence score
        best_idx = torch.argmax(results["scores"]).item()
        best_box = boxes[best_idx].cpu().numpy().tolist()

        # 2. Generate Binary Mask via SAM
        sam_inputs = self.sam_processor(
            pil_img, 
            input_boxes=[[[best_box]]], 
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            sam_outputs = self.sam_model(**sam_inputs)

        masks = self.sam_processor.image_processor.post_process_masks(
            sam_outputs.pred_masks.cpu(),
            sam_inputs["original_sizes"].cpu(),
            sam_inputs["reshaped_input_sizes"].cpu()
        )

        full_ruler_mask = (masks[0][0][0].numpy() * 255).astype(np.uint8)

        # 3. POST-PROCESSING: SUBTRACT PINK INCHES STRIPE
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        
        # Magenta / Pink in OpenCV HSV space (8-bit: H = 0..180)
        lower_pink = np.array([130, 50, 70])
        upper_pink = np.array([175, 255, 255])
        pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)

        # Dilate the pink mask slightly to cover edge bleeding/blur
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        pink_mask_dilated = cv2.dilate(pink_mask, kernel, iterations=1)

        # Keep ONLY the non-pink pixels inside the SAM mask
        cm_ruler_mask = cv2.bitwise_and(full_ruler_mask, cv2.bitwise_not(pink_mask_dilated))

        # Morphological open to remove tiny isolated specks
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cm_ruler_mask = cv2.morphologyEx(cm_ruler_mask, cv2.MORPH_OPEN, kernel_clean)

        return cm_ruler_mask