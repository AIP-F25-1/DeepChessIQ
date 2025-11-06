# model_imitation.py
from __future__ import annotations
from typing import Tuple
import torch
import torch.nn as nn

class ImitationPolicy(nn.Module):
    def __init__(self, obs_size: int, action_space: int, hidden=(512, 256)):
        super().__init__()
        layers = []
        last = obs_size
        for h in hidden:
            layers += [nn.Linear(last, h), nn.ReLU()]
            last = h
        self.pi = nn.Sequential(*layers, nn.Linear(last, action_space))
        self.vf = nn.Sequential(nn.Linear(obs_size, 256), nn.ReLU(), nn.Linear(256, 1))

    def forward(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        logits = self.pi(obs)   # unmasked logits
        value = self.vf(obs).squeeze(1)
        return logits, value
