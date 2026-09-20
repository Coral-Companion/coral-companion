import os
import cv2
import torch
import numpy as np
import torchvision.models as models
import torchvision.transforms as transforms

EMBEDDING_DIMENSION = 512

# Re-direct the framework to point inside our local packaged directory path
local_weights_dir = os.path.join(os.getcwd(), "weights")
os.environ["TORCH_HOME"] = local_weights_dir

device = torch.device("cpu")

resnet_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
resnet_model = torch.nn.Sequential(*list(resnet_model.children())[:-1])
resnet_model.eval()

transform_pipeline = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

class EmbeddingService:
    """
    An embedding is a vector representation of an image using Resnet 18. It will be used to determine 
    similarity of two corals and whether it is the same colony or not (not the same species, but the
    same individual). Images of the same coral colony will result in similar embeddings even if the 
    lighting or the camera angle is different.
    """
    
    

    def generate_vector_embedding(self, image):
        """ Transforms an OpenCV image matrix into a 512-dimension spatial vector array. """
        # TODO: decide how to proceed with transparency. Maybe use a tighter mask using alpha? For now ignore alpha channel.
        if image.shape[2] == 4:
            rgb_img = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)        
        tensor_img = transform_pipeline(rgb_img).unsqueeze(0).to(device)
        
        with torch.inference_mode():
            embedding_tensor = torch.squeeze(resnet_model(tensor_img))
            embedding = embedding_tensor.cpu().numpy()
            
            # Normalizing is not _really_ necessary but it will standarize the length of all vectors to 1
            norm = np.linalg.norm(embedding)
            embedding = embedding / norm
            return embedding.tolist()
        