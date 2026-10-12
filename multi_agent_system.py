#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULTI-AGENT SYSTEM (Berdasarkan referensi STEKOM)
====================================================
Sistem AI Multi-Agen berbasis Python menggunakan:
- MCP (Model Context Protocol) untuk context management
- A2A (Agent-to-Agent) untuk komunikasi antar-agen

Struktur:
    SuperAgen (Kepala)
    ├── RingkasanAgen (SummaryAgent)
    ├── AnalisisAgen (AnalysisAgent)
    ├── ReviewAgen (ReviewAgent)
    └── EvaluasiAgen (EvaluationAgent)
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re


# ============================================================
# MCP (MODEL CONTEXT PROTOCOL) - Simulasi
# ============================================================
class MCPProtocol:
    """
    Simulasi MCP (Model Context Protocol) untuk manajemen context.
    Setiap agen memiliki memory dari MCP.
    """

    def __init__(self):
        self.context_memory = {}  # Agen -> Context
        self.memory_tiers = {
            "tier1_global": {},      # Global knowledge
            "tier2_declarative": {},  # Facts & knowledge
            "tier3_procedural": {},   # Skills & procedures
            "tier4_reactive": {},     # Quick responses
        }

    def add_context(self, agent_id: str, context: str, tier: str = "tier2_declarative"):
        """Add context to MCP memory."""
        if agent_id not in self.context_memory:
            self.context_memory[agent_id] = []
        self.context_memory[agent_id].append({
            "content": context[:200],
            "tier": tier,
            "timestamp": datetime.now().isoformat(),
        })
        return True

    def get_context(self, agent_id: str, top_n: int = 3) -> List[Dict]:
        """Get context for agent."""
        if agent_id not in self.context_memory:
            return []
        return self.context_memory[agent_id][-top_n:]

    def get_all_memory(self) -> Dict:
        """Get all memory by agent."""
        return self.context_memory

    def update_tier(self, agent_id: str, tier: str, data: Dict):
        """Update memory tier."""
        if tier in self.memory_tiers:
            self.memory_tiers[tier][agent_id] = data


# ============================================================
# A2A (AGENT-TO-AGENT) PROTOCOL
# ============================================================
class A2AProtocol:
    """
    Simulasi A2A (Agent-to-Agent) protocol untuk komunikasi.
    """

    def __init__(self):
        self.agents = {}
        self.messages = []

    def register_agent(self, agent_id: str, agent_obj: Any):
        """Register agent."""
        self.agents[agent_id] = agent_obj

    def call_agent(self, caller_id: str, agent_id: str, task: str) -> Dict:
        """
        Call another agent.
        Returns response.
        """
        if agent_id not in self.agents:
            return {"error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]
        response = agent.process(task)

        # Log
        msg = {
            "from": caller_id,
            "to": agent_id,
            "task": task[:100],
            "response": str(response)[:200],
            "timestamp": datetime.now().isoformat(),
        }
        self.messages.append(msg)

        return response

    def get_message_history(self, limit: int = 10) -> List[Dict]:
        """Get message history."""
        return self.messages[-limit:]


# ============================================================
# AGENT BASE CLASS
# ============================================================
class Agent:
    """
    Base class for all agents.
    """

    def __init__(self, name: str, agent_type: str, mcp: MCPProtocol, a2a: A2AProtocol):
        self.name = name
        self.agent_type = agent_type
        self.mcp = mcp
        self.a2a = a2a
        self.tasks = []

    def process(self, task: str) -> Dict:
        """Process a task."""
        raise NotImplementedError

    def register(self):
        """Register self to A2A protocol."""
        self.a2a.register_agent(self.name, self)


# ============================================================
# SUB-AGENTS (Dasar dari referensi STEKOM)
# ============================================================
class SummaryAgent(Agent):
    """
    Agent untuk membuat ringkasan.
    Based on: Ringkasan skill
    """

    def __init__(self, mcp: MCPProtocol, a2a: A2AProtocol):
        super().__init__("RingkasanAgen", "summary", mcp, a2a)

    def process(self, task: str) -> Dict:
        """Process summary task."""
        # Simulate summary generation
        summary = self._create_summary(task)
        self.mcp.add_context(self.name, summary, "tier4_reactive")
        return {
            "agent": self.name,
            "type": "summary",
            "summary": summary,
            "score": self._summarize_score(summary),
            "timestamp": datetime.now().isoformat(),
        }

    def _create_summary(self, text: str) -> str:
        """Create summary from text."""
        # Simple extractive summary
        sentences = re.split(r'[.!?]', text)
        key_sentences = []
        for s in sentences:
            if any(kw in s.lower() for kw in ['ringkasan', 'kesimpulan', 'poin', 'hasil', 'kategori']):
                key_sentences.append(s.strip())
        if key_sentences:
            return ' '.join(key_sentences[:3])
        return text[:200] + "..." if len(text) > 200 else text

    def _summarize_score(self, summary: str) -> float:
        """Score summary quality."""
        words = len(summary.split())
        if words < 10:
            return 40
        elif words < 30:
            return 60
        elif words < 60:
            return 80
        else:
            return 85


class AnalysisAgent(Agent):
    """
    Agent untuk analisis konten.
    Based on: Analisis skill
    """

    def __init__(self, mcp: MCPProtocol, a2a: A2AProtocol):
        super().__init__("AnalisisAgen", "analysis", mcp, a2a)

    def process(self, task: str) -> Dict:
        """Process analysis task."""
        analysis = self._analyze_content(task)
        self.mcp.add_context(self.name, str(analysis), "tier2_declarative")
        return {
            "agent": self.name,
            "type": "analysis",
            "analysis": analysis,
            "score": self._analyze_score(analysis),
            "timestamp": datetime.now().isoformat(),
        }

    def _analyze_content(self, text: str) -> Dict:
        """Analyze content and return structured data."""
        content_lower = text.lower()
        categories = []

        if "ringkasan" in content_lower or "poin" in content_lower:
            categories.append("summary_related")
        if "analisis" in content_lower or "hasil" in content_lower:
            categories.append("analysis_related")
        if "kategori" in content_lower:
            categories.append("categorized")
        if "kritik" in content_lower or "saran" in content_lower:
            categories.append("reviewed")

        return {
            "categories": categories,
            "topic_count": len(categories),
            "keywords_found": categories,
            "timestamp": datetime.now().isoformat(),
        }

    def _analyze_score(self, analysis: Dict) -> float:
        """Score analysis quality."""
        topics = analysis.get("topic_count", 0)
        if topics >= 3:
            return 85
        elif topics >= 2:
            return 70
        else:
            return 55


class ReviewAgent(Agent):
    """
    Agent untuk review/ulasan.
    Based on: Review skill
    """

    def __init__(self, mcp: MCPProtocol, a2a: A2AProtocol):
        super().__init__("ReviewAgen", "review", mcp, a2a)

    def process(self, task: str) -> Dict:
        """Process review task."""
        review = self._create_review(task)
        self.mcp.add_context(self.name, review, "tier4_reactive")
        return {
            "agent": self.name,
            "type": "review",
            "review": review,
            "score": self._review_score(review),
            "timestamp": datetime.now().isoformat(),
        }

    def _create_review(self, text: str) -> str:
        """Create review/feedback."""
        positives = ["baik", "bagus", "mantap", "terbaik", "lengkap"]
        negatives = ["kurang", "terlalu", "perlu", "karena", "jika"]

        pos_count = sum(1 for p in positives if p in text.lower())
        neg_count = sum(1 for n in negatives if n in text.lower())

        if pos_count > neg_count:
            feedback = "Konten ini memiliki kualitas baik. Pertahankan gaya penulisan yang jelas."
        else:
            feedback = "Tambahkan pendukung lebih banyak dan perjelas struktur kesimpulan."

        return f"Review: {feedback} (Positives: {pos_count}, Negatives: {neg_count})"

    def _review_score(self, review: str) -> float:
        """Score review quality."""
        if "Kualitas baik" in review:
            return 80
        elif "Tambahkan" in review:
            return 60
        else:
            return 50


class EvaluationAgent(Agent):
    """
    Agent untuk evaluasi.
    Based on: Evaluation skill
    """

    def __init__(self, mcp: MCPProtocol, a2a: A2AProtocol):
        super().__init__("EvaluasiAgen", "evaluation", mcp, a2a)

    def process(self, task: str) -> Dict:
        """Process evaluation task."""
        score = self._evaluate(task)
        self.mcp.add_context(self.name, f"Eval: {score}", "tier1_global")
        return {
            "agent": self.name,
            "type": "evaluation",
            "score": score,
            "decision": self._decide(score),
            "timestamp": datetime.now().isoformat(),
        }

    def _evaluate(self, content: str) -> float:
        """Evaluate content."""
        if not content:
            return 0

        if len(content) < 20:
            return 20
        elif len(content) < 100:
            return 50
        elif len(content) < 300:
            return 70
        elif len(content) < 500:
            return 85
        else:
            return 90

    def _decide(self, score: float) -> str:
        """Decision based on score."""
        if score >= 80:
            return "BAIK"
        elif score >= 70:
            return "CUKUP"
        else:
            return "PERLU DIUBAH"


# ============================================================
# SUPER-AGENT (Kepala)
# ============================================================
class SuperAgent:
    """
    Super-agent (Kepala) yang mengkoordinasikan sub-agents.
    Based on: Manning Book - Adaptive Harness
    """

    def __init__(self, name: str = "SuperAgent", result_dir: str = "agent_results"):
        self.name = name
        self.result_dir = Path(result_dir)
        self.result_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.mcp = MCPProtocol()
        self.a2a = A2AProtocol()
        self.sub_agents = {}
        self.learning_log = []
        self.skills = {
            "ringkasan": 42.0, "analisis": 38.0, "review": 54.0,
            "translate": 40.0, "question": 42.0, "classify": 28.0, "evaluate": 43.0
        }

        # Create sub-agents
        self._create_sub_agents()

    def _create_sub_agents(self):
        """Create sub-agents based on references."""
        # Create sub-agents
        self.agents = [
            SummaryAgent(self.mcp, self.a2a),
            AnalysisAgent(self.mcp, self.a2a),
            ReviewAgent(self.mcp, self.a2a),
            EvaluationAgent(self.mcp, self.a2a),
        ]

        # Register all agents
        for agent in self.agents:
            agent.register()
            self.sub_agents[agent.name] = agent

    def process_task(self, task: str, task_type: str = "auto") -> Dict:
        """
        Process task through appropriate agent.
        Based on: Manning book - Self-improvement loop
        """
        print(f"\n{'='*60}")
        print(f" TASK: {task[:50]}...")
        print(f"{'='*60}")

        # Determine which agent to use
        if task_type == "auto":
            task_type = self._classify_task(task)

        # Find appropriate agent
        agent_map = {
            "summary": "RingkasanAgen",
            "analysis": "AnalisisAgen",
            "review": "ReviewAgen",
            "evaluation": "EvaluasiAgen",
        }

        agent_name = agent_map.get(task_type, "ReviewAgen")
        agent = self.sub_agents[agent_name]

        # Call agent via A2A
        result = self.a2a.call_agent("SuperAgent", agent_name, task)

        # Update skill based on result
        skill_id = self._map_agent_to_skill(agent_name)
        if skill_id:
            self._update_skill(skill_id, result.get("score", 50))

        # Record
        self.learning_log.append({
            "task": task[:100],
            "agent": agent_name,
            "type": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })

        # Save
        self._save_progress()

        return result

    def _classify_task(self, task: str) -> str:
        """Classify task type."""
        content_lower = task.lower()
        if "ringkasan" in content_lower:
            return "summary"
        elif "analisis" in content_lower or "kategori" in content_lower:
            return "analysis"
        elif "review" in content_lower or "kritik" in content_lower or "saran" in content_lower:
            return "review"
        else:
            return "evaluation"

    def _map_agent_to_skill(self, agent_name: str) -> str:
        """Map agent to skill."""
        mapping = {
            "RingkasanAgen": "ringkasan",
            "AnalisisAgen": "analisis",
            "ReviewAgen": "review",
            "EvaluasiAgen": "evaluate",
        }
        return mapping.get(agent_name, "evaluate")

    def _update_skill(self, skill_id: str, score: float):
        """Update skill rating."""
        if skill_id in self.skills:
            # Adaptive training
            if score >= 70:
                self.skills[skill_id] = min(100, self.skills[skill_id] + 2)
            elif score >= 50:
                self.skills[skill_id] = max(0, self.skills[skill_id] + 0.5)
            else:
                self.skills[skill_id] = max(0, self.skills[skill_id] - 1)

    def _save_progress(self):
        """Save progress."""
        with open(self.result_dir / "learning_log.json", "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2, ensure_ascii=False)

        with open(self.result_dir / "multi_agent_state.json", "w", encoding="utf-8") as f:
            json.dump({
                "agents": {k: v.name for k, v in self.sub_agents.items()},
                "skills": self.skills,
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

    def get_report(self) -> Dict:
        """Get report."""
        avg_skill = sum(self.skills.values()) / max(1, len(self.skills))
        return {
            "summary": {
                "total_tasks": len(self.learning_log),
                "avg_skill": round(avg_skill, 1),
                "agents_active": len(self.sub_agents),
            },
            "skills": self.skills,
            "learning_log": self.learning_log,
            "timestamp": datetime.now().isoformat(),
        }


# ======= TEST =======
if __name__ == "__main__":
    print("=" * 60)
    print(" MULTI-AGENT SYSTEM TEST")
    print("=" * 60)

    # Create super agent
    agent = SuperAgent()

    # Test tasks
    tasks = [
        ("Buat ringkasan dari teks ini: Proses pembelajaran agent disebut...",
         "summary"),
        ("Analisis kategori teks: " + "ringkasan poin hasil kategori".upper(),
         "analysis"),
        ("Review kualitas teks ini: Ringkasan ini bagus dan lengkap.",
         "review"),
        ("Evaluasi kualitas teks ini: Ringkasan ini bagus.", "evaluation"),
    ]

    for task, task_type in tasks:
        result = agent.process_task(task, task_type)
        print(f"   Result: {result.get('score', 'N/A')}")
        print()

    # Final report
    report = agent.get_report()
    print("\n=== FINAL REPORT ===")
    print(f"   Agents active: {report['summary']['agents_active']}")
    print(f"   Total tasks: {report['summary']['total_tasks']}")
    print(f"   Average skill: {report['summary']['avg_skill']:.1f}")
    print("\n   Skills:")
    for skill, rating in report['skills'].items():
        print(f"      {skill}: {rating:.1f}")

    print("\n   Directory:", agent.result_dir)
    print("   Files: learning_log.json, multi_agent_state.json")
    print("=" * 60)
