# masking_model.py
from __future__ import annotations
from typing import Dict, List

import torch
import torch.nn as nn
from ray.rllib.models.torch.torch_modelv2 import TorchModelV2
from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.utils.framework import try_import_torch
from ray.rllib.models import ModelCatalog
from ray.rllib.policy.view_requirement import ViewRequirement
from ray.rllib.utils.torch_utils import FLOAT_MIN

torch, nn = try_import_torch()

class MaskedFCPolicy(TorchModelV2, nn.Module):
    """
    Simple MLP that reads {"obs": vec, "action_mask": mask} and applies the mask to logits.
    """
    def __init__(self, obs_space, action_space, num_outputs, model_config, name):
        TorchModelV2.__init__(self, obs_space, action_space, num_outputs, model_config, name)
        nn.Module.__init__(self)

        obs_size = obs_space.original_space["obs"].shape[0]
        hidden = model_config.get("fcnet_hiddens", [512, 256])

        layers: List[nn.Module] = []
        last = obs_size
        for h in hidden:
            layers += [nn.Linear(last, h), nn.ReLU()]
            last = h
        self.pi = nn.Sequential(*layers, nn.Linear(last, action_space.n))  # unmasked logits
        self.vf = nn.Sequential(nn.Linear(obs_size, 256), nn.ReLU(), nn.Linear(256, 1))

        self._cur_value = None

    def forward(self, input_dict, state, seq_lens):
        obs_vec = input_dict["obs"]["obs"].float()
        mask = input_dict["obs"]["action_mask"]

        logits = self.pi(obs_vec)

        # Apply mask: set illegal logits to very negative
        inf_mask = torch.clamp(torch.log(mask), min=FLOAT_MIN)  # 0 -> -inf
        masked_logits = logits + inf_mask

        self._cur_value = self.vf(obs_vec).squeeze(1)
        return masked_logits, state

    def value_function(self):
        return self._cur_value

# Register
ModelCatalog.register_custom_model("masked_fc_policy", MaskedFCPolicy)
