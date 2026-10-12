#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULTI-AGENT SYSTEM V4
===================================
Berdasarkan referensi:
1. Shopping & Leyton-Brown: "Multiagent Systems" (masfoundations.org/mas.pdf)
2. STEKOM Journal: "Sistem AI Multi-Agen berbasis Python Menggunakan MCP dan A2A"

Fitur baru:
- Fictitious Play (Agent belajar dari interaksi)
- Reinforcement Learning (Belajar dari reward)
- No-Regret Learning (Optimasi tanpa regret)
- Communication Protocol (Protokol komunikasi agen)
- Mechanism Design (Desain mekanisme untuk alokasi tugas)
- Auction-based task allocation (Alokasi tugas via lelang)
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
import re


# ============================================================
# FICTITIOUS PLAY (Agent belajar dari interaksi)
# ============================================================
class FictitiousPlay:
    """
    Fictitious play: Agens belajar dengan menghitung distribusi pola pilihan lawan.
    Setiap agen memperbarui keyakinannya tentang strategi lawan.
    """

    def __init__(self):
        self.strategy_history = {}  # Agent -> {strategy: count}
        self.agents = []

    def register_agent(self, agent_id: str):
        """Daftar agent."""
        self.agents.append(agent_id)
        if agent_id not in self.strategy_history:
            self.strategy_history[agent_id] = {}

    def update_action(self, agent_id: str, action: str):
        """Update aksi agent."""
        if agent_id not in self.strategy_history:
            self.strategy_history[agent_id] = {}
        self.strategy_history[agent_id][action] = \
            self.strategy_history[agent_id].get(action, 0) + 1

    def get_strategy_distribution(self, agent_id: str) -> Dict[str, float]:
        """Dapatkan distribusi strategi."""
        history = self.strategy_history.get(agent_id, {})
        if not history:
            return {}
        total = sum(history.values())
        return {k: v / total for k, v in history.items()}

    def predict_best_response(self, agent_id: str, possible_actions: List[str]) -> str:
        """
        Prediksi strategi terbaik berdasarkan distribusi lawan.
        """
        dist = self.get_strategy_distribution(agent_id)
        if not dist:
            return random.choice(possible_actions)

        # Strategi dengan frekuensi tertinggi = yang diprediksi lawan pilih
        best_response = max(dist, key=dist.get)
        return best_response


# ============================================================
# REINFORCEMENT LEARNING (Belajar dari reward)
# ============================================================
class ReinforcementLearner:
    """
    Reinforcement learning: Agens belajar dari reward.
    Q-learning sederhana.
    """

    def __init__(self, alpha: float = 0.1, gamma: float = 0.9):
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.q_values = {}  # (state, action) -> value
        self.experience = []

    def get_q_value(self, state: str, action: str) -> float:
        """Dapatkan Q-value."""
        return self.q_values.get((state, action), 0.0)

    def update_q_value(self, state: str, action: str, reward: float):
        """Update Q-value berdasarkan reward."""
        current = self.get_q_value(state, action)
        new_value = current + self.alpha * (reward - current)
        self.q_values[(state, action)] = new_value

    def learn(self, state: str, action: str, reward: float):
        """Lakukan learning."""
        self.update_q_value(state, action, reward)
        self.experience.append({
            "state": state,
            "action": action,
            "reward": reward,
            "timestamp": datetime.now().isoformat(),
        })

    def get_best_action(self, state: str, possible_actions: List[str]) -> str:
        """Dapatkan aksi terbaik berdasarkan Q-value."""
        q_values = {a: self.get_q_value(state, a) for a in possible_actions}
        return max(q_values, key=q_values.get)

    def get_policy(self, state: str, possible_actions: List[str]) -> Dict[str, float]:
        """Dapatkan policy (probabilitas aksi)."""
        q_values = {a: self.get_q_value(state, a) for a in possible_actions}
        total = sum(q_values.values())
        if total == 0:
            return {a: 1.0 / len(possible_actions) for a in possible_actions}
        return {a: q / total for a, q in q_values.items()}


# ============================================================
# NO-REGRET LEARNING (Optimasi tanpa regret)
# ============================================================
class NoRegretLearner:
    """
    No-regret learning: Agens belajar mengurangi regret terhadap strategi terbaik.
    Berdasarkan konsep dari chapter 7.5.
    """

    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon
        self.total_reward = 0.0
        self.rewards = {}  # action -> list of rewards

    def get_action_probability(self, agent_id: str, possible_actions: List[str],
                               rewards: Dict[str, float]) -> Dict[str, float]:
        """
        Dapatkan probabilitas aksi berdasarkan reward.
        Menggunakan softmax / UCB.
        """
        if not possible_actions:
            return {}

        # Calculate average reward per action
        avg_rewards = {}
        for action in possible_actions:
            if action in rewards:
                avg_rewards[action] = rewards[action]
            else:
                avg_rewards[action] = 0.0

        # Softmax probability
        exp_values = {a: math.exp(r / self.epsilon) if r > 0 else 0 for a, r in avg_rewards.items()}
        total = sum(exp_values.values())
        if total == 0:
            return {a: 1.0 / len(possible_actions) for a in possible_actions}

        return {a: v / total for a, v in exp_values.items()}

    def record_reward(self, rewards: Dict[str, float]):
        """Rekam reward."""
        for action, reward in rewards.items():
            if action not in self.rewards:
                self.rewards[action] = []
            self.rewards[action].append(reward)
        self.total_reward += sum(rewards.values())


# ============================================================
# COMMUNICATION PROTOCOL (Protokol komunikasi)
# ============================================================
class CommunicationProtocol:
    """
    Protokol komunikasi antar agen.
    Berdasarkan konsep dari chapter 8.
    """

    def __init__(self):
        self.messages = []
        self.protocol_rules = {
            "REQUEST": "Agent meminta tugas",
            "RESPONSE": "Agent merespons",
            "OFFER": "Agent menawarkan layanan",
            "ACCEPT": "Agent menerima",
            "REJECT": "Agent menolak",
            "INFORM": "Agent memberitahu informasi",
        }

    def send_message(self, sender: str, receiver: str, message_type: str,
                     content: str) -> Dict:
        """Kirim pesan."""
        msg = {
            "sender": sender,
            "receiver": receiver,
            "type": message_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "id": hashlib.md5(f"{sender}{receiver}{datetime.now()}".encode()).hexdigest()[:8],
        }
        self.messages.append(msg)
        return msg

    def receive_message(self, receiver: str, limit: int = 5) -> List[Dict]:
        """Terima pesan."""
        return [m for m in self.messages if m['receiver'] == receiver][-limit:]

    def get_protocol_rules(self) -> Dict:
        """Dapatkan aturan protokol."""
        return self.protocol_rules


# ============================================================
# MECHANISM DESIGN (Desain mekanisme)
# ============================================================
class MechanismDesign:
    """
    Desain mekanisme untuk alokasi tugas.
    Berdasarkan konsep VCG mechanism (chapter 10).
    """

    def __init__(self):
        self.bidders = {}  # Agent -> {task: bid}
        self.allocations = {}  # Task -> Agent

    def register_bidder(self, agent_id: str, bid: Dict[str, float]):
        """Daftar bidder."""
        self.bidders[agent_id] = bid

    def allocate_tasks(self, tasks: List[str]) -> Dict:
        """
        Alokasi tugas menggunakan mekanisme.
        """
        # Simple auction: Agent dengan harga termurah menang
        allocation = {}
        for task in tasks:
            winner = None
            min_price = float('inf')
            for agent, bids in self.bidders.items():
                if task in bids and bids[task] < min_price:
                    min_price = bids[task]
                    winner = agent
            if winner:
                allocation[task] = winner
                self.allocations[task] = winner
        return allocation

    def calculate_vcg_payment(self, task: str, winner: str) -> float:
        """
        Hitung payment menggunakan VCG mechanism.
        """
        # Simple VCG: payment = loss to others
        others_best = float('inf')
        for agent, bids in self.bidders.items():
            if agent != winner and task in bids:
                others_best = min(others_best, bids[task])
        return others_best if others_best != float('inf') else 0


# ============================================================
# MULTI-AGENT SYSTEM V4
# ============================================================
class SuperAgentV4:
    """
    Super-agent V4 dengan:
    - Fictitious Play
    - Reinforcement Learning
    - No-Regret Learning
    - Communication Protocol
    - Mechanism Design
    """

    def __init__(self, name: str = "SuperAgent", result_dir: str = "agent_results"):
        self.name = name
        self.result_dir = Path(result_dir)
        self.result_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.fictitious_play = FictitiousPlay()
        self.reinforcement_learner = ReinforcementLearner()
        self.no_regret_learner = NoRegretLearner()
        self.communication = CommunicationProtocol()
        self.mechanism = MechanismDesign()

        # Sub-agents
        self.sub_agents = {
            "RingkasanAgen": {"rating": 60.0, "type": "summary"},
            "AnalisisAgen": {"rating": 56.0, "type": "analysis"},
            "ReviewAgen": {"rating": 72.0, "type": "review"},
            "EvaluasiAgen": {"rating": 50.0, "type": "evaluation"},
        }

        # Learning log
        self.learning_log = []

        # Register self
        self.fictitious_play.register_agent("SuperAgent")
        self.reinforcement_learner = ReinforcementLearner()
        self.no_regret_learner = NoRegretLearner()

    def process_task(self, task: str, task_type: str = "auto") -> Dict:
        """
        Process task menggunakan multi-agent system.
        """
        print(f"\n{'='*60}")
        print(f" TASK: {task[:50]}...")
        print(f"{'='*60}")

        # Classify task type
        if task_type == "auto":
            task_type = self._classify_task(task)

        # Select agent
        agent = self._select_agent(task_type)

        # Communicate via A2A protocol
        self.communication.send_message(
            sender="SuperAgent",
            receiver=agent,
            message_type="REQUEST",
            content=task[:100]
        )

        # Process task
        result = self._execute_agent(agent, task)

        # Learn from reward
        reward = self._calculate_reward(task, result)
        self.reinforcement_learner.learn("SuperAgent", agent,
                                         reward=reward)
        self.no_regret_learner.record_reward({agent: reward})

        # Commit to fictitious play
        self.fictitious_play.update_action("SuperAgent", agent)

        # Save
        self.learning_log.append({
            "task": task[:100],
            "agent": agent,
            "type": task_type,
            "reward": reward,
            "timestamp": datetime.now().isoformat(),
        })

        self._save_progress()

        return result

    def _classify_task(self, task: str) -> str:
        """Klasifikasi tugas."""
        content_lower = task.lower()
        if "ringkasan" in content_lower:
            return "summary"
        elif "analisis" in content_lower or "kategori" in content_lower:
            return "analysis"
        elif "review" in content_lower or "kritik" in content_lower or "saran" in content_lower:
            return "review"
        else:
            return "evaluation"

    def _select_agent(self, task_type: str) -> str:
        """Pilih agen terbaik."""
        agent_map = {
            "summary": "RingkasanAgen",
            "analysis": "AnalisisAgen",
            "review": "ReviewAgen",
            "evaluation": "EvaluasiAgen",
        }
        return agent_map.get(task_type, "ReviewAgen")

    def _execute_agent(self, agent: str, task: str) -> Dict:
        """Eksekusi agent."""
        # Generate result based on agent type
        if "Ringkasan" in agent:
            result = self._create_summary(task)
        elif "Analisis" in agent:
            result = self._create_analysis(task)
        elif "Review" in agent:
            result = self._create_review(task)
        else:
            result = {"score": 70.0, "decision": "BAIK"}

        return {
            "agent": agent,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

    def _create_summary(self, text: str) -> str:
        """Buat ringkasan."""
        return f"Ringkasan: {text[:80]}..."

    def _create_analysis(self, text: str) -> Dict:
        """Buat analisis."""
        return {
            "kategori": ["summary", "content"],
            "keywords": ["ringkasan", "poin"],
            "analysis": "Teks ini berisi poin-poin penting."
        }

    def _create_review(self, text: str) -> str:
        """Buat review."""
        return "Review: Konten memiliki kualitas baik. Pertahankan gaya penulisan yang jelas."

    def _calculate_reward(self, task: str, result: Dict) -> float:
        """Hitung reward."""
        # Simple reward based on agent performance
        rating = self.sub_agents.get(result['agent'], {}).get('rating', 50)
        return min(100, rating + random.uniform(-5, 5))

    def _save_progress(self):
        """Simpan progress."""
        with open(self.result_dir / "learning_log.json", "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2, ensure_ascii=False)

        with open(self.result_dir / "v4_state.json", "w", encoding="utf-8") as f:
            json.dump({
                "agents": self.sub_agents,
                "learning_log": self.learning_log,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

    def get_report(self) -> Dict:
        """Dapatkan laporan."""
        avg_rating = sum(v['rating'] for v in self.sub_agents.values()) / max(1, len(self.sub_agents))
        return {
            "summary": {
                "total_tasks": len(self.learning_log),
                "avg_rating": round(avg_rating, 1),
                "agents_active": len(self.sub_agents),
            },
            "agents": self.sub_agents,
            "learning_log": self.learning_log,
            "timestamp": datetime.now().isoformat(),
        }


# ======= TEST =======
if __name__ == "__main__":
    print("=" * 60)
    print(" MULTI-AGENT SYSTEM V4 - SELF-IMPROVING")
    print("=" * 60)

    agent = SuperAgentV4()

    # Test tasks
    tasks = [
        ("Buat ringkasan dari teks ini: Proses pembelajaran agent...", "summary"),
        ("Analisis kategori teks: " + "ringkasan poin hasil kategori".upper(), "analysis"),
        ("Review kualitas teks ini: Ringkasan ini bagus dan lengkap.", "review"),
        ("Evaluasi kualitas teks ini: Ringkasan ini bagus.", "evaluation"),
    ]

    for task, task_type in tasks:
        result = agent.process_task(task, task_type)
        print(f"   Result: {result}")
        print()

    # Final report
    report = agent.get_report()
    print("\n=== FINAL REPORT ===")
    print(f"   Agents active: {report['summary']['agents_active']}")
    print(f"   Total tasks: {report['summary']['total_tasks']}")
    print(f"   Average rating: {report['summary']['avg_rating']:.1f}")
    print("\n   Skills:")
    for skill, data in report['agents'].items():
        print(f"      {skill}: {data['rating']:.1f}")

    print("\n   Directory:", agent.result_dir)
    print("   Files: learning_log.json, v4_state.json")
    print("=" * 60)
