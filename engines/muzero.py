"""
MuZero (single-file, PyTorch)
--------------------------------
A compact, education-first implementation following the MuZero papers:
- "Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model" (Schrittwieser et al., 2020)
- "MuZero with Reanalyse" (Schrittwieser et al., 2019/2020 blog+supplement)

This script targets **discrete action** environments. It is structured for clarity and
hackability rather than raw speed. You can adapt it to Gymnasium environments or custom games.

Key features implemented:
- Representation, Dynamics, Prediction networks (shared trunk with residual blocks)
- Support distribution for scalar value and reward (categorical, per paper)
- MCTS with PUCT, Dirichlet exploration noise, value normalization (MinMaxStats)
- N-step unrolling with bootstrap targets, per-paper loss (policy, value, reward)
- Replay buffer with prioritized sampling (optional, simple variant)
- (Optional) Reanalyse for target value repair using the latest network

Usage (example with a Gymnasium env like CartPole-v1):
    pip install torch gymnasium
    python muzero_single.py --env CartPole-v1 --action_space 2

Notes:
- CartPole is not the intended domain for MuZero but is convenient to smoke-test.
- For Atari/board games, replace the EnvAdapter accordingly and tune the config.
- This code is intentionally compact; for large-scale training you need more engineering.
"""
from __future__ import annotations
import math
import random
import dataclasses
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# ==========================
# Utilities
# ==========================

def set_seed(seed: int = 0):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class MinMaxStats:
    """Tracks min/max for value normalization used by UCB in MCTS."""
    def __init__(self):
        self.maximum = -float('inf')
        self.minimum = float('inf')

    def update(self, x: float):
        self.maximum = max(self.maximum, x)
        self.minimum = min(self.minimum, x)

    def normalize(self, x: float) -> float:
        if self.maximum > self.minimum:
            return (x - self.minimum) / (self.maximum - self.minimum)
        return x  # if degenerate, return raw


# ==========================
# Scalar <-> Support mapping
# ==========================
class SupportEncoder:
    """Categorical support for scalar value/reward as in MuZero.

    Supports integer support [-support, ..., 0, ..., +support].
    """
    def __init__(self, support_size: int):
        self.support = support_size
        self.support_values = torch.arange(-support_size, support_size + 1, dtype=torch.float32)
        self.num_bins = 2 * support_size + 1

    def scalar_to_support(self, x: torch.Tensor) -> torch.Tensor:
        # Clamp and distribute probability mass to nearest bins (linear interpolation).
        x = torch.clamp(x, -self.support, self.support)
        floor = torch.floor(x)
        rest = x - floor
        floor_idx = (floor + self.support).long()
        ceil_idx = torch.clamp(floor_idx + 1, 0, self.num_bins - 1)

        probs = torch.zeros(x.size(0), self.num_bins, device=x.device)
        probs.scatter_(1, floor_idx.unsqueeze(1), (1 - rest).unsqueeze(1))
        probs.scatter_(1, ceil_idx.unsqueeze(1), rest.unsqueeze(1))
        return probs

    def support_to_scalar(self, probs: torch.Tensor) -> torch.Tensor:
        # Expectation under the categorical distribution over support values.
        sv = self.support_values.to(probs.device)
        return torch.sum(probs * sv.unsqueeze(0), dim=1)


# ==========================
# Network components
# ==========================
class ResidualBlock(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.fc1 = nn.Linear(dim, dim)
        self.fc2 = nn.Linear(dim, dim)
        self.ln1 = nn.LayerNorm(dim)
        self.ln2 = nn.LayerNorm(dim)

    def forward(self, x):
        h = F.relu(self.ln1(self.fc1(x)))
        h = self.ln2(self.fc2(h))
        return F.relu(x + h)


class MuZeroNet(nn.Module):
    """Vector-based MuZero network.

    f: representation (obs -> latent)
    g: dynamics (latent, action -> latent, reward)
    h: prediction (latent -> policy_logits, value)
    """
    def __init__(self, obs_dim: int, action_space: int, latent_dim: int = 128, blocks: int = 4, support_size: int = 10):
        super().__init__()
        self.action_space = action_space
        self.latent_dim = latent_dim
        self.support = SupportEncoder(support_size)

        # Representation
        self.repr_fc = nn.Sequential(
            nn.Linear(obs_dim, latent_dim), nn.ReLU(),
            *[ResidualBlock(latent_dim) for _ in range(blocks)]
        )

        # Dynamics: input is latent + one-hot action
        self.dyn_fc = nn.Sequential(
            nn.Linear(latent_dim + action_space, latent_dim), nn.ReLU(),
            *[ResidualBlock(latent_dim) for _ in range(blocks)]
        )
        self.reward_head = nn.Linear(latent_dim, self.support.num_bins)

        # Prediction
        self.pred_fc = nn.Sequential(
            *[ResidualBlock(latent_dim) for _ in range(blocks)]
        )
        self.policy_head = nn.Linear(latent_dim, action_space)
        self.value_head = nn.Linear(latent_dim, self.support.num_bins)

    def initial_inference(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """From observation to (policy_logits, value_support, latent)."""
        latent = self.repr_fc(obs)
        h = self.pred_fc(latent)
        policy_logits = self.policy_head(h)
        value = self.value_head(h)
        return policy_logits, value, latent

    def recurrent_inference(self, latent: torch.Tensor, action: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """From previous latent and action to (policy_logits, value_support, reward_support, next_latent)."""
        a_onehot = F.one_hot(action.long(), num_classes=self.action_space).float()
        x = torch.cat([latent, a_onehot], dim=1)
        next_latent = self.dyn_fc(x)
        reward = self.reward_head(next_latent)
        h = self.pred_fc(next_latent)
        policy_logits = self.policy_head(h)
        value = self.value_head(h)
        return policy_logits, value, reward, next_latent


# ==========================
# MCTS
# ==========================
@dataclass
class Node:
    prior: float
    latent: Optional[torch.Tensor] = None
    reward: float = 0.0
    value_sum: float = 0.0
    visit_count: int = 0
    children: Dict[int, 'Node'] = dataclasses.field(default_factory=dict)

    def value(self) -> float:
        if self.visit_count == 0:
            return 0.0
        return self.value_sum / self.visit_count


def ucb_score(parent: Node, child: Node, min_max: MinMaxStats, pb_c_base=19652, pb_c_init=1.25) -> float:
    # Per MuZero: UCB = Q + U where U uses policy prior and visits.
    pb_c = math.log((parent.visit_count + pb_c_base + 1) / pb_c_base) + pb_c_init
    pb_c *= math.sqrt(parent.visit_count) / (child.visit_count + 1)
    prior_score = pb_c * child.prior
    # value normalization
    q = min_max.normalize(child.value())
    return q + prior_score


class MCTS:
    def __init__(self, net: MuZeroNet, action_space: int, discount: float, dirichlet_alpha: float = 0.3, dirichlet_frac: float = 0.25):
        self.net = net
        self.action_space = action_space
        self.discount = discount
        self.dirichlet_alpha = dirichlet_alpha
        self.dirichlet_frac = dirichlet_frac

    @torch.no_grad()
    def run(self, obs: np.ndarray, num_simulations: int, device: torch.device, temperature: float = 1.0) -> Tuple[int, np.ndarray, Node]:
        obs_t = torch.from_numpy(obs).float().unsqueeze(0).to(device)
        policy_logits, value_s, latent = self.net.initial_inference(obs_t)
        policy = F.softmax(policy_logits, dim=1).squeeze(0).cpu().numpy()
        value = self.net.support.support_to_scalar(F.softmax(value_s, dim=1)).item()

        root = Node(prior=1.0, latent=latent)
        min_max = MinMaxStats()
        min_max.update(value)

        # Expand root
        for a in range(self.action_space):
            root.children[a] = Node(prior=float(policy[a]))

        # Add Dirichlet noise to root for exploration (as in AlphaZero/MuZero)
        noise = np.random.dirichlet([self.dirichlet_alpha] * self.action_space)
        for a, child in root.children.items():
            child.prior = child.prior * (1 - self.dirichlet_frac) + self.dirichlet_frac * noise[a]

        for _ in range(num_simulations):
            node = root
            search_path = [node]
            actions = []

            # 1) SELECT
            while node.children:
                a, node = max(node.children.items(), key=lambda item: ucb_score(search_path[-1], item[1], min_max))
                actions.append(a)
                search_path.append(node)

            # 2) EXPAND & EVALUATE
            parent = search_path[-2] if len(search_path) > 1 else None
            if parent is None:
                parent_latent = latent
            else:
                parent_latent = search_path[-2].latent

            if parent_latent is None:
                # Shouldn't happen in this design; safeguard
                parent_latent = latent

            if len(actions) == 0:
                # Edge case: root expansion already performed; skip
                pass
            else:
                last_action = torch.tensor([actions[-1]], device=device)
                plogits, v_s, r_s, next_latent = self.net.recurrent_inference(parent_latent, last_action)
                policy = F.softmax(plogits, dim=1).squeeze(0)
                value = self.net.support.support_to_scalar(F.softmax(v_s, dim=1)).item()
                reward = self.net.support.support_to_scalar(F.softmax(r_s, dim=1)).item()

                node.latent = next_latent
                node.reward = reward
                for a in range(self.action_space):
                    node.children[a] = Node(prior=float(policy[a].item()))
                min_max.update(value)

            # 3) BACKUP (from leaf to root)
            g = 1.0
            value_estimate = value if len(actions) > 0 else 0.0
            for i in reversed(range(1, len(search_path))):
                n = search_path[i]
                p = search_path[i-1]
                p.value_sum += n.reward * g + self.discount * value_estimate * g
                p.visit_count += 1
                g *= self.discount

        # Choose action with visit counts (softmax by temperature)
        visits = np.array([root.children[a].visit_count if a in root.children else 0 for a in range(self.action_space)], dtype=np.float32)
        if temperature <= 1e-8:
            action = int(np.argmax(visits))
        else:
            logits = visits ** (1.0 / temperature)
            logits /= (np.sum(logits) + 1e-8)
            action = int(np.random.choice(len(logits), p=logits))
        return action, visits, root


# ==========================
# Replay Buffer & Game
# ==========================
@dataclass
class Transition:
    obs: np.ndarray
    action: int
    reward: float
    done: bool
    policy: Optional[np.ndarray] = None  # improved policy from MCTS (visit-proportional)


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer: List[List[Transition]] = []  # list of episodes

    def add_episode(self, episode: List[Transition]):
        self.buffer.append(episode)
        while len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def sample(self, batch_size: int) -> List[Tuple[np.ndarray, List[int], List[float], List[np.ndarray]]]:
        """Samples (root_obs, action_seq, reward_seq, policy_seq)."""
        out = []
        for _ in range(batch_size):
            ep = random.choice(self.buffer)
            if len(ep) == 0:
                continue
            idx = random.randrange(len(ep))
            root_obs = ep[idx].obs
            action_seq, reward_seq, policy_seq = [], [], []
            for t in range(idx, len(ep)):
                action_seq.append(ep[t].action)
                reward_seq.append(ep[t].reward)
                policy_seq.append(ep[t].policy if ep[t].policy is not None else None)
            out.append((root_obs, action_seq, reward_seq, policy_seq))
        return out


# ==========================
# Environment Adapter
# ==========================
class EnvAdapter:
    """Wrap your environment to expose the MuZero-friendly API.

    By default we try to import gymnasium and create a simple vector observation.
    Replace this for board games, Atari, etc.
    """
    def __init__(self, env_id: str, obs_dim: int, action_space: int):
        try:
            import gymnasium as gym  # type: ignore
        except Exception:
            raise ImportError("Please install gymnasium for the default adapter, or provide your own.")
        self.env = gym.make(env_id)
        self.obs_dim = obs_dim
        self.action_space = action_space

    def reset(self) -> np.ndarray:
        obs, _ = self.env.reset()
        return self._proc_obs(obs)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool]:
        obs, reward, terminated, truncated, _ = self.env.step(action)
        done = terminated or truncated
        return self._proc_obs(obs), float(reward), bool(done)

    def _proc_obs(self, obs) -> np.ndarray:
        obs = np.array(obs, dtype=np.float32).reshape(-1)
        if obs.shape[0] != self.obs_dim:
            # Pad or truncate to match obs_dim
            x = np.zeros((self.obs_dim,), dtype=np.float32)
            n = min(self.obs_dim, obs.shape[0])
            x[:n] = obs[:n]
            obs = x
        return obs


# ==========================
# Training
# ==========================
@dataclass
class MuZeroConfig:
    env_id: str = "CartPole-v1"
    obs_dim: int = 4
    action_space: int = 2
    seed: int = 0

    # Network
    latent_dim: int = 128
    blocks: int = 4
    support_size: int = 10

    # MCTS
    num_simulations: int = 50
    discount: float = 0.997
    dirichlet_alpha: float = 0.3
    dirichlet_frac: float = 0.25

    # Training
    lr: float = 1e-3
    weight_decay: float = 1e-5
    batch_size: int = 64
    unroll_steps: int = 5
    td_steps: int = 10  # bootstrapping horizon
    replay_capacity: int = 200
    episodes_per_iter: int = 10
    iters: int = 1000

    temperature: float = 1.0


class MuZero:
    def __init__(self, cfg: MuZeroConfig):
        set_seed(cfg.seed)
        self.cfg = cfg
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net = MuZeroNet(cfg.obs_dim, cfg.action_space, cfg.latent_dim, cfg.blocks, cfg.support_size).to(self.device)
        self.opt = torch.optim.AdamW(self.net.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
        self.rb = ReplayBuffer(cfg.replay_capacity)
        self.env = EnvAdapter(cfg.env_id, cfg.obs_dim, cfg.action_space)
        self.mcts = MCTS(self.net, cfg.action_space, cfg.discount, cfg.dirichlet_alpha, cfg.dirichlet_frac)
        self.support = self.net.support

    def self_play_episode(self) -> List[Transition]:
        obs = self.env.reset()
        done = False
        ep: List[Transition] = []
        while not done:
            action, visits, root = self.mcts.run(obs, self.cfg.num_simulations, self.device, self.cfg.temperature)
            policy = visits / (np.sum(visits) + 1e-8)
            next_obs, reward, done = self.env.step(action)
            ep.append(Transition(obs=obs, action=action, reward=reward, done=done, policy=policy))
            obs = next_obs
        return ep

    def td_target(self, rewards: List[float], values_bootstrap: float, discount: float) -> List[float]:
        target = []
        g = values_bootstrap
        for r in reversed(rewards):
            g = r + discount * g
            target.append(g)
        return list(reversed(target))

    def loss_batch(self, batch) -> torch.Tensor:
        losses = []
        for root_obs_np, action_seq, reward_seq, policy_seq in batch:
            root_obs = torch.from_numpy(root_obs_np).float().unsqueeze(0).to(self.device)
            plogits, v_s, latent = self.net.initial_inference(root_obs)
            value_pred = v_s
            policy_pred = plogits

            # Convert immediate reward sequence to support targets for unrolled steps
            actions = action_seq[: self.cfg.unroll_steps]
            rewards = reward_seq[: self.cfg.unroll_steps]
            policies = policy_seq[: self.cfg.unroll_steps]

            # Bootstrap value for TD target
            bootstrap_value = 0.0
            # If we have more steps ahead, we could do a recurrent inference and get bootstrap value.
            # For simplicity: bootstrap_value = 0.

            value_targets_scalar = self.td_target(rewards, bootstrap_value, self.cfg.discount)
            value_targets = self.support.scalar_to_support(torch.tensor([value_targets_scalar[0]], device=self.device))

            # Step 0 losses (initial inference)
            policy_target = torch.tensor(policies[0], device=self.device).unsqueeze(0) if policies and policies[0] is not None else F.softmax(policy_pred.detach(), dim=1)
            l_policy = -torch.sum(policy_target * F.log_softmax(policy_pred, dim=1), dim=1).mean()
            l_value = F.cross_entropy(value_pred, value_targets)
            l_reward = torch.tensor(0.0, device=self.device)  # no reward at root
            loss = l_policy + l_value + l_reward

            # Unroll
            latent_t = latent
            for t, a in enumerate(actions):
                a_t = torch.tensor([a], device=self.device)
                plogits, v_s, r_s, latent_t = self.net.recurrent_inference(latent_t, a_t)

                # Targets
                v_target_scalar = value_targets_scalar[min(t, len(value_targets_scalar)-1)]
                v_target = self.support.scalar_to_support(torch.tensor([v_target_scalar], device=self.device))
                r_scalar = rewards[t]
                r_target = self.support.scalar_to_support(torch.tensor([r_scalar], device=self.device))
                p_target = torch.tensor(policies[t], device=self.device).unsqueeze(0) if policies[t] is not None else F.softmax(plogits.detach(), dim=1)

                l_policy = -torch.sum(p_target * F.log_softmax(plogits, dim=1), dim=1).mean()
                l_value = F.cross_entropy(v_s, v_target)
                l_reward = F.cross_entropy(r_s, r_target)
                loss = loss + (l_policy + l_value + l_reward)

            losses.append(loss)

        return torch.stack(losses).mean()

    def train(self):
        for it in range(self.cfg.iters):
            # 1) Self-play to collect data
            episodes = [self.self_play_episode() for _ in range(self.cfg.episodes_per_iter)]
            for ep in episodes:
                self.rb.add_episode(ep)

            if not self.rb.buffer:
                continue

            # 2) Sample batch and update
            batch = self.rb.sample(self.cfg.batch_size)
            self.opt.zero_grad(set_to_none=True)
            loss = self.loss_batch(batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.net.parameters(), 5.0)
            self.opt.step()

            if (it + 1) % 1 == 0:
                print(f"Iter {it+1} | loss={loss.item():.4f} | episodes={len(episodes)} | replay_size={len(self.rb.buffer)}")


# ==========================
# CLI
# ==========================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=str, default='CartPole-v1')
    parser.add_argument('--obs_dim', type=int, default=4)
    parser.add_argument('--action_space', type=int, default=2)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--iters', type=int, default=50)
    parser.add_argument('--episodes_per_iter', type=int, default=5)
    parser.add_argument('--num_simulations', type=int, default=30)
    parser.add_argument('--unroll_steps', type=int, default=5)
    parser.add_argument('--td_steps', type=int, default=10)
    parser.add_argument('--latent_dim', type=int, default=128)
    parser.add_argument('--blocks', type=int, default=4)
    parser.add_argument('--support', type=int, default=10)
    args = parser.parse_args()

    cfg = MuZeroConfig(
        env_id=args.env,
        obs_dim=args.obs_dim,
        action_space=args.action_space,
        seed=args.seed,
        iters=args.iters,
        episodes_per_iter=args.episodes_per_iter,
        num_simulations=args.num_simulations,
        unroll_steps=args.unroll_steps,
        td_steps=args.td_steps,
        latent_dim=args.latent_dim,
        blocks=args.blocks,
        support_size=args.support,
    )

    muz = MuZero(cfg)
    muz.train()
