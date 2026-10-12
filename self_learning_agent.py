#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELF-LEARNING SYSTEM
=====================
Autonomous learning with analysis & selection.

Komponen:
1. ContentAnalyzer  : Menganalisa konten (video, text, audio)
2. KnowledgeSelector: Memilih yang relevan
3. AutoEvaluator   : Menilai hasil (before/after)
4. LearningLog     : Menyimpan progres
5. SelfLearning    : Integrasi lengkap

CARA GUNA:
>>> from self_learning import SelfLearning
>>> learner = SelfLearning()
>>> result = learner.learn_from_source("video", transcript)
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


# ============================================================
# 1. CONTENT ANALYZER (Menganalisa konten)
# ============================================================
class ContentAnalyzer:
    """Menganalisa konten untuk menemukan knowledge points."""

    def __init__(self):
        self.knowledge_base = {
            "reflection": {
                "keywords": ["reflect", "critic", "improve", "mistake", "weakness", "flaw", "answer"],
                "description": "Agent generates answer, criticizes it, then improves it"
            },
            "memory": {
                "keywords": ["memory", "store", "recall", "context", "conversation", "prefer"],
                "description": "Agent stores experiences and applies them later"
            },
            "evaluation": {
                "keywords": ["score", "select", "best", "option", "candidate", "evaluate"],
                "description": "Agent generates multiple options and selects the best"
            },
            "agent_orchestration": {
                "keywords": ["orchestrator", "sub-agents", "A2A", "delegate", "multi-agent"],
                "description": "Coordination of multiple agents"
            },
        }

    def analyze(self, content: str) -> Dict:
        """
        Analyze content, return knowledge points.
        """
        content_lower = content.lower()
        topics_found = []

        for topic, config in self.knowledge_base.items():
            if any(kw in content_lower for kw in config["keywords"]):
                topics_found.append(topic)

        return {
            "topics_found": topics_found,
            "relevance_score": self._calculate_relevance(content, topics_found),
            "knowledge_extracted": self._extract_knowledge(content, topics_found),
        }

    def _calculate_relevance(self, content: str, topics: List[str]) -> float:
        """Calculate relevance score (0-100)."""
        if not topics:
            return 0
        base_score = len(topics) * 10
        if len(content) > 500:
            base_score += 10
        elif len(content) > 200:
            base_score += 5
        return min(base_score, 100)

    def _extract_knowledge(self, content: str, topics: List[str]) -> Dict:
        """Extract knowledge based on topics."""
        extracted = {}
        for topic in topics:
            extracted[topic] = self._extract_topic_specific(content, topic)
        return extracted

    def _extract_topic_specific(self, content: str, topic: str) -> str:
        """Extract specific content for each topic."""
        content_lower = content.lower()
        if "reflection" in topic.lower():
            return "Agent generates answer -> Critic -> Improves -> Final"
        elif "memory" in topic.lower():
            return "Short-term + Long-term memory for context"
        elif "evaluation" in topic.lower():
            return "Generate options -> Score -> Select best"
        elif "agent_orchestration" in topic.lower():
            return "Multi-agent coordination with A2A protocol"
        return content[:100]


# ============================================================
# 2. KNOWLEDGE SELECTOR (Memilih yang relevan)
# ============================================================
class KnowledgeSelector:
    """Memilih knowledge yang relevan berdasarkan skor."""

    def __init__(self, threshold: int = 60):
        self.threshold = threshold
        self.knowledge_base = {}

    def select(self, content: str, topics: List[str], threshold: int = None) -> List[Dict]:
        """
        Select relevant knowledge based on score.
        """
        threshold = threshold or self.threshold
        selected = []

        for topic in topics:
            score = self._calculate_topic_score(content, topic)
            if score >= threshold:
                # Extract relevant section from content
                content_snippet = self._extract_relevant_section(content, topic)
                selected.append({
                    "topic": topic,
                    "score": score,
                    "content": content_snippet,
                })

        return sorted(selected, key=lambda x: x["score"], reverse=True)

    def _extract_relevant_section(self, content: str, topic: str) -> str:
        """Extract relevant section from content based on topic."""
        content_lower = content.lower()
        
        # Find relevant section based on topic
        if "reflection" in topic.lower():
            keywords = ["reflection", "answer", "critic", "improve", "self-assess"]
            for kw in keywords:
                if kw in content_lower:
                    idx = content_lower.find(kw)
                    return content[max(0, idx-50):idx+200]
        elif "memory" in topic.lower():
            keywords = ["memory", "store", "recall", "context"]
            for kw in keywords:
                if kw in content_lower:
                    idx = content_lower.find(kw)
                    return content[max(0, idx-50):idx+200]
        elif "evaluation" in topic.lower():
            keywords = ["score", "select", "best", "option", "evaluate"]
            for kw in keywords:
                if kw in content_lower:
                    idx = content_lower.find(kw)
                    return content[max(0, idx-50):idx+200]
        elif "agent_orchestration" in topic.lower():
            keywords = ["orchestrator", "sub-agents", "A2A", "delegates"]
            for kw in keywords:
                if kw in content_lower:
                    idx = content_lower.find(kw)
                    return content[max(0, idx-50):idx+200]
        
        # Fallback: return first 200 chars
        return content[:200]

    def _calculate_topic_score(self, content: str, topic: str) -> float:
        """Calculate relevance score for specific topic."""
        content_lower = content.lower()
        if "reflection" in topic.lower():
            return 75 if "critic" in content_lower else 30
        elif "memory" in topic.lower():
            return 70 if "memory" in content_lower else 20
        elif "evaluation" in topic.lower():
            return 75 if "score" in content_lower else 25
        elif "agent_orchestration" in topic.lower():
            return 60 if "orchestrator" in content_lower else 20
        return 50

    def update_knowledge(self, topic: str, content: str, score: float):
        """Update knowledge base."""
        self.knowledge_base[topic] = {
            "content": content,
            "score": score,
            "timestamp": datetime.now().isoformat(),
        }

    def get_best(self, topic: str = None) -> Dict:
        """Get best knowledge for topic."""
        if topic:
            return self.knowledge_base.get(topic)
        return self.knowledge_base

    def get_all(self) -> Dict:
        """Get all knowledge."""
        return self.knowledge_base


# ============================================================
# 3. AUTO EVALUATOR (Menilai hasil)
# ============================================================
class AutoEvaluator:
    """Menilai hasil dari self-learning."""

    def __init__(self):
        self.learning_log = []

    def evaluate_upgrade(self, task: str, before_score: float, after_score: float,
                         agent_name: str = "demo") -> Dict:
        """
        Evaluate the improvement after upgrade.
        """
        improvement = after_score - before_score

        result = {
            "task": task,
            "before_score": before_score,
            "after_score": after_score,
            "improvement": improvement,
            "decision": self._decide_action(improvement),
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
        }

        self.learning_log.append(result)
        return result

    def _decide_action(self, improvement: float) -> str:
        """Decide action based on improvement."""
        if improvement >= 10:
            return "UPGRADED"
        elif improvement >= 0:
            return "MAINTAIN"
        else:
            return "ROLLBACK"

    def get_summary(self) -> Dict:
        """Get learning summary."""
        if not self.learning_log:
            return {"total_tasks": 0, "total_improvement": 0, "avg_improvement": 0}

        total_improvement = sum(x["improvement"] for x in self.learning_log)
        avg_improvement = total_improvement / len(self.learning_log)

        return {
            "total_tasks": len(self.learning_log),
            "total_improvement": total_improvement,
            "avg_improvement": round(avg_improvement, 1),
            "successful_upgrades": sum(1 for x in self.learning_log if x["improvement"] >= 0),
        }


# ============================================================
# 4. LEARNING LOG (Menyimpan progres)
# ============================================================
class LearningLog:
    """Menyimpan progres belajar."""

    def __init__(self, log_dir: str = "agent_results"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.learning_log_path = self.log_dir / "learning_log.json"
        self.logs = []

    def save(self, data: Dict):
        """Simpan data."""
        self.logs.append(data)
        with open(self.log_dir / "learning_log.json", "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)

    def get_all(self) -> List[Dict]:
        """Dapatkan semua log."""
        return self.logs

    def clear(self):
        """Hapus semua log."""
        self.logs = []


# ============================================================
# 5. SELF-LEARNING AGENT (Integrasi lengkap)
# ============================================================
class SelfLearningAgent:
    """
    Agent yang bisa belajar dari sumber (video, text, audio) dan meningkatkan skill.
    """

    def __init__(self,
                 name: str = "KepalaAgen",
                 result_dir: str = "agent_results",
                 learning_threshold: float = 70.0):
        self.name = name
        self.learning_threshold = learning_threshold

        # Component
        self.analyzer = ContentAnalyzer()
        self.selector = KnowledgeSelector(threshold=60)
        self.evaluator = AutoEvaluator()
        self.learning_log = LearningLog(result_dir)

        # Agent state
        self.agents = {}
        self.results = []
        self.logs = []
        self.tasks = []  # Task queue

        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load existing data."""
        self.learning_log_path = self.learning_log.log_dir / "learning_log.json"
        if self.learning_log_path.exists():
            with open(self.learning_log_path, "r", encoding="utf-8") as f:
                self.learning_log.logs = json.load(f)

    def analyze(self, content: str) -> Dict:
        """Menganalisa konten."""
        return self.analyzer.analyze(content)

    def select(self, content: str, topics: List[str]) -> List[Dict]:
        """Memilih knowledge yang relevan."""
        return self.selector.select(content, topics)

    def integrate(self, knowledge: Dict) -> Dict:
        """
        Integrasi knowledge ke dalam agen.
        """
        for topic, data in knowledge.items():
            self.selector.update_knowledge(topic, data, 0)
        return {"status": "integrated", "topics": list(knowledge.keys())}

    def evaluate(self, before: float, after: float, task: str) -> Dict:
        """
        Evaluasi perbaikan.
        """
        return self.evaluator.evaluate_upgrade(task, before, after)

    def save(self, data: Dict):
        """Simpan data."""
        self.learning_log.save(data)
        self.logs.append(data)

    def get_progress(self) -> Dict:
        """Dapatkan summary progres."""
        return self.evaluator.get_summary()

    def get_knowledge(self, topic: str = None) -> Dict:
        """Dapatkan knowledge."""
        return self.selector.get_all() if topic is None else self.selector.get_best(topic)

    def run(self, task_name: str, content: str) -> Dict:
        """
        Main learning loop.
        """
        print(f"\n{'='*60}")
        print(f" LEARNING START: {task_name}")
        print(f"="*60)

        # 1. Analyze
        analysis = self.analyzer.analyze(content)
        print(f"\n[1] ANALYZE: {analysis['topics_found']}")
        print(f"    Relevance: {analysis['relevance_score']}/100")

        # 2. Select
        if analysis["relevance_score"] >= 60:
            selected = self.selector.select(content, analysis["topics_found"])
            print(f"    Selected: {len(selected)} topics")

            # 3. Integrate
            for item in selected:
                self.selector.update_knowledge(
                    item["topic"],
                    item["content"],
                    item["score"]
                )
            print(f"    Integrated: {len(selected)} topics")

            # 4. Save
            self.save({
                "type": "analysis",
                "content": content,
                "analysis": analysis,
                "selected": selected,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "status": "UPGRADED",
                "topics": analysis["topics_found"],
                "relevance": analysis["relevance_score"],
                "selected": selected
            }

        return {"status": "SKIPPED", "reason": "Too low relevance"}

    def evaluate_upgrade(self, task: str, before: float, after: float, agent_name: str = "demo"):
        """Evaluate upgrade."""
        return self.evaluator.evaluate_upgrade(task, before, after, agent_name)

    def get_progress(self) -> Dict:
        """Get progress summary."""
        return self.evaluator.get_summary()


# ============================================================
# PENGGUNAAN CONTOH
# ============================================================
def main():
    """Alur utama."""
    print("=" * 60)
    print(" SELF-LEARNING SYSTEM")
    print("=" * 60)

    # Setup
    learner = SelfLearningAgent()

    # Load video transcript
    with open("video_transcript.txt", encoding="utf-8") as f:
        video_content = f.read()

    # 1. Analyze
    print("\n[1] ANALYZING VIDEO TRANSCRIPT...")
    analysis = learner.analyzer.analyze(video_content)
    print(f"   Topics found: {analysis['topics_found']}")
    print(f"   Relevance: {analysis['relevance_score']}/100")

    # 2. Select
    selected = learner.selector.select(video_content, analysis["topics_found"])
    print(f"\n[2] SELECT: {len(selected)} topics selected")

    # 3. Integrate
    for item in selected:
        learner.selector.update_knowledge(item["topic"], item["content"], item["score"])
    print(f"\n[3] INTEGRATED: {len(selected)} topics")

    # 4. Save
    learner.save({
        "type": "video",
        "content": video_content,
        "analysis": analysis,
        "selected": selected,
        "timestamp": datetime.now().isoformat()
    })
    print(f"\n[4] SAVED to {learner.learning_log.log_dir / 'learning_log.json'}")

    # 5. Progress
    print(f"\n[5] PROGRESS: {learner.get_progress()}")

    # 6. Run tasks
    print("\n" + "=" * 60)
    print(" RUNNING TASKS (Self-Learning Demo)")
    print("=" * 60)

    # Register demo agent
    def demo_agent(payload: str) -> str:
        return f"Ringkasan dari: {str(payload)[:80]}..."

    learner.agents["demo"] = demo_agent

    # Add tasks
    learner.add_task("Tugas 1", "Contoh teks 1")
    learner.add_task("Tugas 2", "Contoh teks 2")
    learner.add_task("Tugas 3", "Contoh teks 3")

    # Run tasks
    results = learner.run_tasks()
    print(f"\n[6] TASKS COMPLETED: {len(results)} tasks")
    print(f"    Average score: {learner.get_progress()['avg_improvement']:.1f}")

    # Summary
    print("\n" + "=" * 60)
    print(" LEARNING SUMMARY")
    print("=" * 60)
    print(f"   Total tasks: {len(results)}")
    print(f"   Average score: {learner.get_progress()['avg_improvement']:.1f}")
    print(f"   Topics learned: {analysis['topics_found']}")


def add_task(self, name: str, payload: str, priority: int = 1) -> Dict:
    """Add task to queue."""
    task_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    task = {
        "task_id": task_id,
        "task_name": name,
        "payload": payload,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None,
        "tasks": []  # Ensure tasks list exists
    }
    if not hasattr(self, 'tasks'):
        self.tasks = []
    self.tasks.append(task)
    return task


def run_tasks(self) -> List[Dict]:
    """Run all pending tasks."""
    results = []
    for task in self.tasks:
        if task["status"] == "pending":
            result = self._run_task(task)
            results.append(result)
    return results


def _run_task(self, task: Dict) -> Dict:
    """Run single task."""
    try:
        # Simulate agent execution
        output = f"Ringkasan dari: {task['payload']}"
        score = 83.3  # Dummy score

        result = {
            "task_id": task["task_id"],
            "task_name": task["task_name"],
            "agent": "demo",
            "output": output,
            "quality_score": 80.0,
            "efficiency_score": 100.0,
            "completeness_score": 70.0,
            "total_score": 83.3,
            "timestamp": datetime.now().isoformat(),
        }

        task["status"] = "done"
        task["completed_at"] = datetime.now().isoformat()
        task["error"] = None

        self.results.append(result)
        return result

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        return {"error": str(e)}


# Check if demo_agent is already defined
if 'demo_agent' not in globals():
    def demo_agent(payload: str) -> str:
        return f"Ringkasan dari: {str(payload)[:80]}..."

    # Patch into SelfLearningAgent class
    SelfLearningAgent.add_task = add_task
    SelfLearningAgent.run_tasks = run_tasks
    SelfLearningAgent._run_task = _run_task
    SelfLearningAgent.demo_agent = demo_agent
    SelfLearningAgent.tugas = main
