# -*- coding: utf-8 -*-
"""utils

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VsfEFy8zhJT2V8I_ecDEH3iYlk-ugCa0
"""

# Transformations and misclassifications.

import albumentations as A
import torch
import torchvision
import torchvision.transforms as transforms
import albumentations as A
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
from torchsummary import summary
from tqdm import tqdm
from torch.optim.lr_scheduler import StepLR
import torch.optim as optim

#from Models import resnet
import matplotlib.pyplot as plt
import numpy as np
#from Models.resnet import *

SEED = 4

#checking the CUDA is available or ?
cuda = torch.cuda.is_available()
print("CUDA Available?", cuda)
num_workers=0
# For reproducibility
torch.manual_seed(SEED)

if cuda:
    torch.cuda.manual_seed(SEED)

# Train Phase transformations
#                                        transforms.RandomCrop(32,padding=4),
#                                        A.Cutout(num_holes=1,max_h_size=16,max_w_size=16),                                         
train_transforms = transforms.Compose([ transforms.RandomCrop(32,padding=4), # randomly flip and rotate
                               transforms.ToTensor(),
                               transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  ])

# Test Phase transformations
test_transforms = transforms.Compose([
                                      #  transforms.Resize((28, 28)),
                                      #  transforms.ColorJitter(brightness=0.10, contrast=0.1, saturation=0.10, hue=0.1),
                                       transforms.ToTensor(),
                                        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
                                       ])
# dataloader arguments - something you'll fetch these from cmdprmt
dataloader_args = dict(shuffle=True, batch_size=60, num_workers=num_workers, pin_memory=True) if cuda else dict(shuffle=True, batch_size=40)

trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                        download=True, transform=train_transforms)


# train dataloader
trainloader = torch.utils.data.DataLoader(trainset, **dataloader_args)
testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                       download=True, transform=test_transforms)
# test dataloader
testloader = torch.utils.data.DataLoader(testset, **dataloader_args)

classes = ('plane', 'car', 'bird', 'cat',
           'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

# to display the images
# functions to show an image
def imshow(img):
    img = img / 2 + 0.5     # unnormalize
    # npimg = img.numpy()
    plt.imshow(np.transpose(img, (1, 2, 0)))



# get some random training images
dataiter = iter(trainloader)
images, labels = next(dataiter)
print(images.shape)
images=images.numpy()
# show images
fig=plt.figure(figsize=(25,4))
#display 50 images
# Display 20 images
for idx in np.arange(20):
      ax = fig.add_subplot(2, 20/2, idx+1, xticks=[], yticks=[])
      imshow(images[idx])
      ax.set_title(classes[labels[idx]])

# We need to convert the images to numpy arrays as tensors are not compatible with matplotlib.
def im_convert(tensor):  
  image = tensor.cpu().clone().detach().numpy() # This process will happen in normal cpu.
  image = image.transpose(1, 2, 0)
  image = image * np.array((0.5, 0.5, 0.5)) + np.array((0.5, 0.5, 0.5))
  image = image.clip(0, 1)
  return image

def misclassification():
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")
    dataiter = iter(testloader)
    images, labels = next(dataiter)
    images = images.to(device)
    labels = labels.to(device)
    output = model(images)
    _, preds = torch.max(output, 1)

    fig = plt.figure(figsize=(25, 4))

    for idx in np.arange(60):
      ax = fig.add_subplot(6, 10, idx+1, xticks=[], yticks=[])
      plt.imshow(im_convert(images[idx]))#gt ground truth
      ax.set_title(" pred {} gt ({})".format(str(classes[preds[idx].item()]), str(classes[labels[idx].item()])), color=("green" if preds[idx]==labels[idx] else "red"))
