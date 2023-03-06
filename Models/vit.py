# -*- coding: utf-8 -*-
"""Vit

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1w3gWJOXx9rmUTSjXvpHLxdaAfwKsFrat
"""

import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torchvision import datasets, transforms
import torchvision
from torchinfo import summary
import torch
from torch import nn

from einops import rearrange, repeat
from einops.layers.torch import Rearrange

def pair(t):
    return t if isinstance(t, tuple) else (t, t)

# classes

class PreNorm(nn.Module):
    def __init__(self, dim, fn):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.fn = fn
    def forward(self, x, **kwargs):
        return self.fn(self.norm(x), **kwargs)

class FeedForward(nn.Module):
    def __init__(self, dim, hidden_dim, dropout = 0.):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, dim),
            nn.Dropout(dropout)
        )
    def forward(self, x):
        return self.net(x)

class Attention(nn.Module):
    def __init__(self, dim,shape,in_channels,out_channels, heads = 8, dim_head = 64, dropout = 0.):
        super().__init__()
        inner_dim = dim_head *  heads
        project_out = not (heads == 1 and dim_head == dim)
        self.shape=shape
        self.heads = heads
        self.dim=dim
        self.dim_head = dim_head
        self.scale = dim_head ** -0.5
       
        self.attend = nn.Softmax(dim = -1)
        #self.to_qkv = nn.Linear(dim, inner_dim * 3, bias = False)
        self.to_keys = nn.Conv2d(in_channels, out_channels, 1)
        self.to_queries = nn.Conv2d(in_channels, out_channels, 1)
        self.to_values = nn.Conv2d(in_channels, out_channels, 1)
        self.unifyheads = nn.Conv2d(out_channels, out_channels, 1)
        self.to_out = nn.Sequential(
            nn.Linear(inner_dim, dim),
            nn.Dropout(dropout)
        ) if project_out else nn.Identity()
        height, width = shape
        self.pos_enc = nn.Parameter(torch.Tensor(self.heads, (2 * height - 1) * (2 * width - 1)))
        self.register_buffer("relative_indices", self.get_indices(height, width))
        self.out1= nn.Flatten(start_dim=1,end_dim=2)
    def forward(self, x):
        #qkv = self.to_qkv(x).chunk(3, dim = -1)
        #q, k, v = map(lambda t: rearrange(t, 'b n (h d) -> b h n d', h = self.heads), qkv)
        #print("shape",x.shape)
        b, _, _ = x.shape
        h,w= self.shape
        #print(self.to_keys(x))
        x=x.permute(2,1,0) # 32,257,128
        keys = self.to_keys(x).view(b, self.heads, self.dim_head, -1)
        #print("keys",keys.shape)
        values = self.to_values(x).view(b, self.heads, self.dim_head, -1)
        queries = self.to_queries(x).view(b, self.heads, self.dim_head, -1)
        q,k,v = queries,keys,values
        dots = torch.matmul(k.transpose(-2, -1),q) * self.scale
        print("dots",dots.shape)
        # indices = self.relative_indices.expand(self.heads, -1)
        # print("indices",indices.shape)
        # rel_pos_enc = self.pos_enc.gather(-1, indices)
        # print("rel",rel_pos_enc.shape)
        # rel_pos_enc = rel_pos_enc.unflatten(-1, (h * w, h * w))
        
        # print("unflatten",rel_pos_enc.shape)
        # att = dots + rel_pos_enc
        # att = dots + rel_pos_enc
        att = F.softmax(dots, dim=-2)
        
        out = values @ att
        #print("out",out.shape)
        #out = out.view(b, -1, h, w)
        out=self.out1(out)
        #print(out.shape)
        out=out.unsqueeze(0)
        out=out.permute(0,2,1,3)
        #print("out1",out.shape)
        out = self.unifyheads(out)
        out=out.squeeze(0)
        out = out.permute(1,2,0)
        #print(out.shape)
        return out
        # att = dots
        # attn = self.attend(att)
        # print("attn",attn.shape)

        # out = torch.matmul(attn, v)
        # print("out_shape", out.shape)
        # out = rearrange(out, 'b h n w -> b n (h w)')
        # out = self.unifyheads(out)

    @staticmethod
    def get_indices(h, w):
        y = torch.arange(h, dtype=torch.long)
        x = torch.arange(w, dtype=torch.long)
        
        y1, x1, y2, x2 = torch.meshgrid(y, x, y, x, indexing='ij')
        indices = (y1 - y2 + h - 1) * (2 * w - 1) + x1 - x2 + w - 1
        indices = indices.flatten()
        
        return indices
class Transformer(nn.Module):
    def __init__(self, dim, depth, heads, dim_head, mlp_dim,shape, dropout = 0.):
        super().__init__()
        self.layers = nn.ModuleList([])
        self.dim=dim
        #self.multiheadattention = MultiheadAttentionConv2d(embed_dim=dim,num_heads=heads, dropout=dropout)
        for _ in range(depth):
            self.layers.append(nn.ModuleList([
                PreNorm(dim, Attention(dim,shape,in_channels=dim,out_channels=dim, heads=heads, dim_head=dim_head)),#, in_channels=dim,out_channels=dim,heads = heads, dim_head = dim_head, dropout = dropout
                PreNorm(dim, FeedForward(dim, mlp_dim, dropout = dropout))
            ]))
    def forward(self, x):
        for attn, ff in self.layers:
            #print(x.shape)
            x = attn(x) + x
            x = ff(x) + x
        return x

class ViT(nn.Module):
    def __init__(self,  image_size, patch_size, num_classes, dim, depth, heads,mlp_dim,  pool = 'cls', channels = 3, dim_head = 64, dropout = 0., emb_dropout = 0.):
        super().__init__()
        image_height, image_width = pair(image_size)
        reduced_size = image_size // patch_size
        shape = (reduced_size, reduced_size)
        
        patch_height, patch_width = pair(patch_size)

        assert image_height % patch_height == 0 and image_width % patch_width == 0, 'Image dimensions must be divisible by the patch size.'

        num_patches = (image_height // patch_height) * (image_width // patch_width)
        patch_dim = channels * patch_height * patch_width
        assert pool in {'cls', 'mean'}, 'pool type must be either cls (cls token) or mean (mean pooling)'

        self.to_patch_embedding = nn.Sequential(
            nn.Conv2d(in_channels=channels,
                                 out_channels=patch_dim,
                                 kernel_size=3,
                                 stride=1,
                                 padding=1),nn.GELU(),nn.Conv2d(in_channels=patch_dim,out_channels=dim,kernel_size=patch_size,stride=patch_size,padding=0),nn.Flatten(start_dim=2, # only flatten the feature map dimensions into a single vector
                                  end_dim=3)
            # Rearrange('b c (h p1) (w p2) -> b (h w) (p1 p2 c)', p1 = patch_height, p2 = patch_width),
            #nn.Linear(patch_dim, dim)
        )
# Create the class token embedding as a learnable parameter that shares the same size as the embedding dimension (D)
        self.pos_embedding = nn.Parameter(torch.randn(1,num_patches + 1, dim),requires_grad=True).cuda( )
        #batch_size=patch_embedding.shape[0]
        #b=128
        
        self.dropout = nn.Dropout(emb_dropout)

        self.transformer = Transformer(dim, depth, heads, dim_head, mlp_dim, shape, dropout)

        self.pool = pool
        self.to_latent = nn.Identity()
        #self.transformer_encoder = nn.Sequential(*[Transformer(dim, depth, heads, dim_head, mlp_dim, shape, dropout) for _ in range(depth)])
        self.mlp_head = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim))
        self.classifier = nn.Sequential(
            nn.Linear(in_features=dim, 
                      out_features=num_classes))
        
        

    def forward(self, img):
        #print("input", img.shape)
        #img = img.unsqueeze(0)
        x = self.to_patch_embedding(img)
        x = x.permute(0,2,1)
        #print("after patch embedding",x.shape)
        b, n, d = x.shape
        batch_size=x.shape[0]
        self.cls_token = nn.Parameter(torch.randn(b,1, dim),requires_grad=True).cuda()
        #cls_tokens = repeat(self.cls_token, '() n d -> b n d', b = batch_size)
        # 7. Prepend class token embedding to patch embedding
        #print("class token",self.cls_token.shape)
        #print("x", x.shape)

        x = torch.cat((self.cls_token, x), dim=1)
        x = x + self.pos_embedding
        #x += self.pos_embedding[:, :(n + 1)]
        x = self.dropout(x)
        #print("before transformer",x.shape)
        x = self.transformer(x)
        #print("after transformer",x.shape)
        # x = x.mean(dim = 1) if self.pool == 'mean' else x[:, 0]
        #print("before latent",x.shape)
        x = self.to_latent(x)
        #print(x.shape)
        #x = x.permute(1,0)
        x = self.mlp_head(x)
        #print("x[:,0]",x[:,0].shape)
        x = self.classifier(x[:,0])
        return x
