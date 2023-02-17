# -*- coding: utf-8 -*-
"""utils

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VsfEFy8zhJT2V8I_ecDEH3iYlk-ugCa0
"""
print("hello")
# Transformations and misclassifications.
from albumentations.pytorch.transforms import ToTensorV2
import cv2
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
from Models import resnet

from Models.resnet import *
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
mean=(0.5, 0.5, 0.5)
std=(0.5, 0.5, 0.5)
def train_transform_function(mean,std):
  train_transform = A.Compose([A.PadIfNeeded(min_height=32+4, min_width=32+4),
                                A.RandomCrop(32,32,always_apply=False,p=1.0), # randomly flip and rotate
                                 A.Cutout(num_holes=1,max_h_size=16,max_w_size=16,fill_value=tuple(mean)), 
                                A.Normalize(mean, std),
                                ToTensorV2(),
                                       ])
  return lambda img:train_transform(image=np.array(img))["image"]
def test_transform_function():
  test_transform = A.Compose([ 
                                A.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                                ToTensorV2(),
                                       ])
  return lambda img:test_transform(image=np.array(img))["image"]
# dataloader arguments - something you'll fetch these from cmdprmt
dataloader_args = dict(shuffle=True, batch_size=60, num_workers=num_workers, pin_memory=True) if cuda else dict(shuffle=True, batch_size=40)

trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                        download=True, transform=train_transform_function(mean,std))


# train dataloader
trainloader = torch.utils.data.DataLoader(trainset, **dataloader_args)
testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                       download=True, transform=test_transform_function())
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




use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")
model =  ResNet18().to(device)

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
    
def viz_data(cols=8, rows=5):
  figure = plt.figure(figsize=(14, 10))
  for i in range(1, cols * rows + 1):
    img, label = exp[i]

    figure.add_subplot(rows, cols, i)
    plt.title(exp.classes[label])
    plt.axis("off")
    plt.imshow(img, cmap="gray")

  plt.tight_layout()
  plt.show()
    
def show_images(aug_dict, ncol=6):
  nrow = len(aug_dict)

  fig, axes = plt.subplots(ncol, nrow, figsize=( 3*nrow, 15), squeeze=False)
  for i, (key, aug) in enumerate(aug_dict.items()):
    for j in range(ncol):
      ax = axes[j,i]
      if j == 0:
        ax.text(0.5, 0.5, key, horizontalalignment='center', verticalalignment='center', fontsize=15)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.axis('off')
      else:
        image, label = exp[j-1]
        if aug is not None:
          transform = A.Compose([aug])
          image = np.array(image)
          image = transform(image=image)['image']
          
        ax.imshow(image)
        ax.set_title(f'{exp.classes[label]}')
        ax.axis('off')

  plt.tight_layout()
  plt.show()
  
# custom dataset class for albumentations library
class AlbumentationImageDataset(Dataset):
  def __init__(self, image_list, train= True):
      self.image_list = image_list
      self.aug = A.Compose({
          A.PadIfNeeded(min_height=32+4,min_width=32+4),
          A.RandomCrop(32,32,always_apply=False,p=1.0),
          A.Normalize((0.49139968, 0.48215841, 0.44653091), (0.24703223, 0.24348513, 0.26158784)),
          A.HorizontalFlip(),
          A.Cutout(1,8,8,fill_value=0.473363),
          # A.CoarseDropout(1, 16, 16, 1, 16, 16,fill_value=0.473363, mask_fill_value=None),
          A.ToGray()
      })

      self.norm = A.Compose({A.Normalize((0.49139968, 0.48215841, 0.44653091), (0.24703223, 0.24348513, 0.26158784)),
      })
      self.train = train
        
  def __len__(self):
      return (len(self.image_list))

  def __getitem__(self, i):
      
      image, label = self.image_list[i]
      
      if self.train:
        #apply augmentation only for training
        image = self.aug(image=np.array(image))['image']
      else:
        image = self.norm(image=np.array(image))['image']
      image = np.transpose(image, (2, 0, 1)).astype(np.float32)
      return torch.tensor(image, dtype=torch.float), label
from torch_lr_finder import LRFinder


def find_lr(net, optimizer, criterion, train_loader):
    """Find learning rate for using One Cyclic LRFinder
    Args:
        net (instace): torch instace of defined model
        optimizer (instance): optimizer to be used
        criterion (instance): criterion to be used for calculating loss
        train_loader (instance): torch dataloader instace for trainig set
    """
    lr_finder = LRFinder(net, optimizer, criterion, device="cuda")
    lr_finder.range_test(train_loader, end_lr=10, num_iter=100, step_mode="exp")
    lr_finder.plot()
    lr_finder.reset()
  
