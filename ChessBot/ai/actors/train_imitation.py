# train_imitation.py
from __future__ import annotations
import math, os
from typing import Dict
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from data_utils import OBS_SIZE, ACTION_SPACE_SIZE
from imitation_dataset import ImitationDataset, load_rows_from_csv, train_val_split
from model_imitation import ImitationPolicy

def masked_log_softmax(logits: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    # mask=0 -> -inf  (avoid nan with clamp)
    inf_mask = torch.clamp(torch.log(mask), min=torch.finfo(logits.dtype).min)
    masked = logits + inf_mask
    return torch.log_softmax(masked, dim=-1)

def cross_entropy_from_probs(log_probs: torch.Tensor, target_probs: torch.Tensor) -> torch.Tensor:
    # CE(p||q) where p = target, q = model -> -sum p * log q
    return -(target_probs * log_probs).sum(dim=-1).mean()

def kl_div_from_probs(log_probs_q: torch.Tensor, target_probs_p: torch.Tensor) -> torch.Tensor:
    # KL(p || q) with log q given: sum p * (log p - log q)
    log_p = torch.log(torch.clamp(target_probs_p, min=1e-12))
    return (target_probs_p * (log_p - log_probs_q)).sum(dim=-1).mean()

def accuracy_top1(logits: torch.Tensor, labels: torch.Tensor) -> float:
    preds = torch.argmax(logits, dim=-1)
    mask = labels >= 0
    if mask.sum() == 0:
        return 0.0
    return (preds[mask] == labels[mask]).float().mean().item()

def train_imitation(
    train_csv: str,
    out_dir: str = "./checkpoints_imitation",
    batch_size: int = 1024,
    lr: float = 3e-4,
    epochs: int = 3,
    lambda_human_ce: float = 1.0,
    lambda_engine_kl: float = 0.2,
    lambda_value: float = 0.2,
    lambda_top1_ce: float = 0.2,        # only applies where label_uci present
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
):
    os.makedirs(out_dir, exist_ok=True)

    rows = load_rows_from_csv(train_csv)
    train_rows, val_rows = train_val_split(rows, val_frac=0.05)
    train_ds = ImitationDataset(train_rows, use_label_top1=True)
    val_ds = ImitationDataset(val_rows, use_label_top1=True)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    model = ImitationPolicy(obs_size=OBS_SIZE, action_space=ACTION_SPACE_SIZE).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)

    best_val = float("inf")
    for epoch in range(1, epochs+1):
        model.train()
        total_loss = total_n = 0
        acc_top1 = 0.0
        for batch in train_loader:
            obs = batch["obs"].to(device)
            mask = batch["mask"].to(device)
            y_human = batch["y_human"].to(device)
            y_engine = batch["y_engine"].to(device)
            label_idx = batch["label_idx"].to(device)

            logits, values = model(obs)
            log_probs = masked_log_softmax(logits, mask)

            loss_human = lambda_human_ce * cross_entropy_from_probs(log_probs, y_human)
            loss_engine = lambda_engine_kl * kl_div_from_probs(log_probs, y_engine)
            # simple value target from human expectation: +0 for now (placeholder)
            loss_value = lambda_value * (values.pow(2).mean())

            # optional top-1 CE if labels exist
            ce_top1 = torch.tensor(0.0, device=device)
            valid = label_idx >= 0
            if valid.any():
                ce_top1 = lambda_top1_ce * nn.functional.cross_entropy(
                    logits[valid], label_idx[valid], reduction="mean"
                )

            loss = loss_human + loss_engine + loss_value + ce_top1
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

            total_loss += loss.item() * obs.size(0)
            total_n += obs.size(0)
            acc_top1 += accuracy_top1(logits.detach(), label_idx) * obs.size(0)

        train_loss = total_loss / max(1, total_n)
        train_acc = acc_top1 / max(1, total_n)

        # ---- validation ----
        model.eval()
        with torch.no_grad():
            v_loss, v_n, v_acc = 0.0, 0, 0.0
            for batch in val_loader:
                obs = batch["obs"].to(device)
                mask = batch["mask"].to(device)
                y_human = batch["y_human"].to(device)
                y_engine = batch["y_engine"].to(device)
                label_idx = batch["label_idx"].to(device)
                logits, values = model(obs)
                log_probs = masked_log_softmax(logits, mask)
                loss_human = lambda_human_ce * cross_entropy_from_probs(log_probs, y_human)
                loss_engine = lambda_engine_kl * kl_div_from_probs(log_probs, y_engine)
                loss_value = lambda_value * (values.pow(2).mean())
                ce_top1 = torch.tensor(0.0, device=device)
                valid = label_idx >= 0
                if valid.any():
                    ce_top1 = lambda_top1_ce * nn.functional.cross_entropy(
                        logits[valid], label_idx[valid], reduction="mean"
                    )
                loss = loss_human + loss_engine + loss_value + ce_top1
                v_loss += loss.item() * obs.size(0)
                v_acc += accuracy_top1(logits, label_idx) * obs.size(0)
                v_n += obs.size(0)
            val_loss = v_loss / max(1, v_n)
            val_acc = v_acc / max(1, v_n)

        print(f"[Epoch {epoch}] train_loss={train_loss:.4f} acc@1={train_acc:.3f} | val_loss={val_loss:.4f} acc@1={val_acc:.3f}")

        # save best
        if val_loss < best_val:
            best_val = val_loss
            path = os.path.join(out_dir, f"policy_epoch{epoch}_valloss{val_loss:.4f}.pt")
            torch.save({"model": model.state_dict(), "obs_size": OBS_SIZE, "action_space": ACTION_SPACE_SIZE}, path)
            print("  ↳ saved:", path)

if __name__ == "__main__":
    # Example:
    # python train_imitation.py -- (edit paths below or use argparse)
    train_csv = os.environ.get("IMITATION_CSV", "./positions_sample.csv")
    train_imitation(train_csv=train_csv)
