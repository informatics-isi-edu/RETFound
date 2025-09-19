
from functools import partial

import timm.models.vision_transformer
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from timm.models.layers import trunc_normal_

class VisionTransformer(timm.models.vision_transformer.VisionTransformer):
    """ Vision Transformer with support for global average pooling
    """
    def __init__(self, global_pool=False, **kwargs):
        super(VisionTransformer, self).__init__(**kwargs)

        self.global_pool = global_pool
        if self.global_pool:
            norm_layer = kwargs['norm_layer']
            embed_dim = kwargs['embed_dim']
            self.fc_norm = norm_layer(embed_dim)

            del self.norm  # remove the original norm

    def forward_features(self, x):
        B = x.shape[0]
        x = self.patch_embed(x)

        cls_tokens = self.cls_token.expand(B, -1, -1)  # stole cls_tokens impl from Phil Wang, thanks
        x = torch.cat((cls_tokens, x), dim=1)
        x = x + self.pos_embed
        x = self.pos_drop(x)

        for blk in self.blocks:
            x = blk(x)

        if self.global_pool:
            x = x[:, 1:, :].mean(dim=1,keepdim=True)  # global pool without cls token
            outcome = self.fc_norm(x)
        else:
            x = self.norm(x)
            outcome = x[:, 0]

        return outcome


def RETFound_mae(**kwargs):
    model = VisionTransformer(
        patch_size=16, embed_dim=1024, depth=24, num_heads=16, mlp_ratio=4, qkv_bias=True,
        norm_layer=partial(nn.LayerNorm, eps=1e-6), **kwargs)
    return model

def RETFound_backbone(**kwargs):
    model = VisionTransformer(
        patch_size=16, embed_dim=128, depth=24, num_heads=16, mlp_ratio=4, qkv_bias=True,
        norm_layer=partial(nn.LayerNorm, eps=1e-6), **kwargs)
    return model

def Dinov2(args, **kwargs):
    
    if args.model_arch == 'dinov2_vits14':
        arch = 'vit_small_patch14_dinov2.lvd142m'
    elif args.model_arch == 'dinov2_vitb14':
        arch = 'vit_base_patch14_dinov2.lvd142m'
    elif args.model_arch == 'dinov2_vitl14':
        arch = 'vit_large_patch14_dinov2.lvd142m'
    elif args.model_arch == 'dinov2_vitg14':
        arch = 'vit_giant_patch14_dinov2.lvd142m'
    else:
        raise ValueError(f"Unknown model_arch '{args.model_arch}'. "
                         f"Expected one of: dinov2_vits14, dinov2_vitb14, dinov2_vitl14, dinov2_vitg14")
        
    model = timm.create_model(
        arch,
        pretrained=True,
        img_size=224,
        **kwargs
    )
    return model



def RETFound_dinov2(args, **kwargs):
    model = timm.create_model(
        'vit_large_patch14_dinov2.lvd142m',
        pretrained=True,
        img_size=224,
        **kwargs
    )
    return model


def Dinov3(args, **kwargs):
    # Load ViT-L/16 backbone (hub model has `head = Identity` by default)
    model = torch.hub.load(
        repo_or_dir="facebookresearch/dinov3",
        model=args.model_arch,
        pretrained=False,   # main() will load your checkpoint
        trust_repo=True,
    )

    # Figure out feature dimension for the probe
    feat_dim = getattr(model, "embed_dim", None) or getattr(model, "num_features", None)
    model.head = nn.Linear(feat_dim, args.nb_classes)
    trunc_normal_(model.head.weight, std=2e-5)
    if model.head.bias is not None:
        nn.init.zeros_(model.head.bias)

    return model

class MultiModalNeuralNetwork(nn.Module):
    
    def __init__(self,img_encoder,modality,num_classes,hidden_dim,inter_dim):
        super().__init__()
        self.img_encoder = img_encoder
        embed_dim = img_encoder.embed_dim
        self.structured = nn.Sequential(
            nn.Linear(modality,hidden_dim),
            nn.ReLU(inplace=True),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(0.1)
        )
        
        self.fusion = nn.Sequential(
            nn.LayerNorm(embed_dim + hidden_dim),
            nn.Linear(embed_dim+hidden_dim,inter_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
            nn.Linear(inter_dim,num_classes)
        )
        
    def forward(self, img, clinical):
        img_emb = self.img_encoder(img)          
        clin_emb = self.structured(clinical)  
        combined = torch.cat([img_emb, clin_emb], dim=-1)  
        out = self.fusion(combined)
        return out

def MultiRETFound_mae(modality, num_classes,hidden_dim, inter_dim, **kwargs):
    if "global_pool" in kwargs:
        kwargs.pop("global_pool")
    if "num_classes" in kwargs:
        kwargs.pop("num_classes")
    vit_encoder = RETFound_mae(num_classes = 0, global_pool = True, **kwargs)
    model = MultiModalNeuralNetwork(img_encoder = vit_encoder,modality = modality, num_classes = num_classes,
                                  hidden_dim = hidden_dim, inter_dim = inter_dim)
    return model

    
def RETFound_reg(**kwargs):
    if "global_pool" in kwargs:
        kwargs.pop("global_pool")
    if "num_classes" in kwargs:
        kwargs.pop("num_classes")
    model = RETFound_backbone(num_classes = 0, global_pool = True, **kwargs)
    return model
