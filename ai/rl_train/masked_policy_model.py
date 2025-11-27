# ai/rl_train/masked_policy_model.py
from typing import Dict, List, Any
from gymnasium import spaces

import torch
import torch.nn as nn
from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.models.torch.torch_modelv2 import TorchModelV2
from ray.rllib.utils.torch_utils import FLOAT_MIN
from ray.rllib.policy.view_requirement import ViewRequirement


class MaskedChessModel(TorchModelV2, nn.Module):
    """Torch model that:
    - Takes {"obs": (8,8,19), "action_mask": (4800,)} as input
    - Applies conv + FC over obs
    - Applies action_mask to logits (invalid -> -inf)
    """

    def __init__(
        self,
        obs_space,
        action_space,
        num_outputs,
        model_config,
        name,
        **kwargs,
    ):
        TorchModelV2.__init__(
            self, obs_space, action_space, num_outputs, model_config, name
        )
        nn.Module.__init__(self)

        # Board planes size
        self._h, self._w, self._c = (8, 8, 19)
        flat_size = self._h * self._w * 32  # after conv

        # Simple conv head (you can tweak)
        self.conv = nn.Sequential(
            nn.Conv2d(self._c, 32, kernel_size=3, padding=1),
            nn.ReLU(),
        )

        hidden_size = 256
        self.policy_head = nn.Sequential(
            nn.Linear(flat_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, action_space.n),
        )

        self.value_head = nn.Sequential(
            nn.Linear(flat_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
        )

        self._value_out = None

        # Tell RLlib we want the action_mask as input
        full_obs_space = model_config.get("obs_space", obs_space)
        if isinstance(full_obs_space, spaces.Dict):
            self.view_requirements["action_mask"] = ViewRequirement(
                space=full_obs_space["action_mask"]
            )
        else:
            # Fallback if not Dict
            pass

    def forward(self, input_dict: Dict[str, Any], state: List[torch.Tensor], seq_lens):
        obs = input_dict["obs"]
        # obs contains keys "obs" and "action_mask"
        board = obs["obs"]  # [B, 8,8,19]
        mask = obs["action_mask"]  # [B, 4800]

        # Convert board to NCHW
        x = board.permute(0, 3, 1, 2)  # [B, C, H, W]
        x = self.conv(x)
        x = torch.flatten(x, start_dim=1)  # [B, -1]

        logits = self.policy_head(x)  # [B, 4800]
        self._value_out = self.value_head(x).squeeze(-1)

        # Apply mask: invalid -> large negative
        inf_mask = torch.clamp(torch.log(mask.float()), min=FLOAT_MIN)
        masked_logits = logits + inf_mask

        return masked_logits, state

    def value_function(self):
        return self._value_out
