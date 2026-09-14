import os
import torch
import torchvision.models as models

def pre_stage_weights():
    print("Pre-downloading ResNet-18 weight parameters for serverless bundling...")
    # Force weights checkpoint down into local folder path reference strings
    target_dir = os.path.join(os.getcwd(), "../weights")
    os.makedirs(target_dir, exist_ok=True)
    
    # Trigger native download to local runtime caches
    os.environ["TORCH_HOME"] = target_dir
    models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    print(f"Weights successfully cached locally within directory: {target_dir}")

if __name__ == "__main__":
    pre_stage_weights()
