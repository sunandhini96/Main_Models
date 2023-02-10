# -*- coding: utf-8 -*-
"""main

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wXxQswUxSlqyZNft-zL2vJfWNQkvFtoR
"""

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

# from google.colab import drive
# drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Github/

# !git init School_of_AI

# Commented out IPython magic to ensure Python compatibility.
# %cd School_of_AI/

# !git status

# !git add .

# !git clone https://github.com/sunandhini96/Main_Models.git

# Commented out IPython magic to ensure Python compatibility.
# %cd Main_Models/

# Commented out IPython magic to ensure Python compatibility.
# %ls -a


# Train and Test loop:



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

use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")
model =  ResNet18().to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
scheduler = StepLR(optimizer, step_size=6, gamma=0.1)

EPOCHS = 20

train_losses = []
test_losses = []
train_acc = []
test_acc = []

def train(model, device, train_loader, optimizer, epoch):
  model.train()
  pbar = tqdm(train_loader)
  correct = 0
  processed = 0
  train_loss=0
  for batch_idx, (data, target) in enumerate(pbar):
    # get samples
    data, target = data.to(device), target.to(device)

    # Init
    optimizer.zero_grad()
    # In PyTorch, we need to set the gradients to zero before starting to do backpropragation because PyTorch accumulates the gradients on subsequent backward passes. 
    # Because of this, when you start your training loop, ideally you should zero out the gradients so that you do the parameter update correctly.

    # Predict
    y_pred = model(data)

    # Calculate loss
    loss = criterion(y_pred, target)
    #train_losses.append(loss)

    # Backpropagation
    loss.backward()
    optimizer.step()
    train_loss+=loss.item()
    # Update pbar-tqdm
    
    pred = y_pred.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
    correct += pred.eq(target.view_as(pred)).sum().item()
  processed += len(data)
  train_loss/=len(train_loader.dataset)
  train_losses.append(train_loss)
  print('\nTrain set: Average loss: {:.4f}, Accuracy: {}/{} ({:.2f}%)\n'.format(
    train_loss, correct, len(train_loader.dataset),
    100. * correct / len(train_loader.dataset)))
  pbar.set_description(desc= f'Loss={loss.item()} Batch_id={batch_idx} Accuracy={100*correct/processed:0.2f}')
  train_acc.append(100*correct/len(train_loader.dataset))

def test(model, device, test_loader):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += criterion(output, target).item()  # sum up batch loss
            pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    test_losses.append(test_loss)

    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.2f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))
    
    test_acc.append(100. * correct / len(test_loader.dataset))
