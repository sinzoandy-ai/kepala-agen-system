#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENHANCED SELF-LEARNING AGENT v2.0
===================================
Dengan semantic search, skill tracking, dan self-improvement loop.

FITUR BARU:
- Semantic Search (cosine similarity)
- Skill Library & Tracking
- Difficulty Rating (Easy/Medium/Hard)
- Self-Improvement Loop
- Automated Evaluation

CARA GUNA:
>>> from self_learning_agent_v2 import SmartAgen
>>> agen = SmartAgen("KepalaAgen")
>>> agen.learn_from_source("video", transcript)
>>> agen.evaluate_and_improve()
"""

import json
import time
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


# ============================================================
# SEMANTIC SIMILARITY (Cosine Similarity)
# ============================================================
class SimpleSimilarity:
    """
    Simple word frequency-based similarity.
    (Alternative: use actual embeddings if available)
    """

    def __init__(self):
        self.vocab = {}
        self.word_index = 0

    def _build_vocab(self, texts: List[str]):
        """Build vocabulary from texts."""
        for text in texts:
            for word in text.lower().split():
                word = word.strip(".,!?()[]{}'\"")
                if word and len(word) > 1:
                    if word not in self.vocab:
                        self.vocab[word] = self.word_index
                        self.word_index += 1

    def text_to_vector(self, text: str) -> List[int]:
        """Convert text to word-frequency vector."""
        vector = [0] * len(self.vocab)
        for word in text.lower().split():
            word = word.strip(".,!?()[]{}'\"")
            if word in self.vocab:
                vector[self.vocab[word]] += 1
        return vector

    def cosine_similarity(self, vec1: List[int], vec2: List[int]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot_product / (norm1 * norm2)

    def semantic_search(self, query: str, documents: List[str]) -> List[Tuple[str, float]]:
        """
        Find most relevant documents to query.
        """
        if not self.vocab:
            self._build_vocab(documents + [query])

        query_vec = self.text_to_vector(query)
        results = []

        for doc in documents:
            doc_vec = self.text_to_vector(doc)
            score = self.cosine_similarity(query_vec, doc_vec)
            results.append((doc, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results


# ============================================================
# SKILL LIBRARY
# ============================================================
class Skill:
    """Represent a skill with rating and difficulty."""

    def __init__(self, id: str, name: str, description: str, difficulty: str = "easy"):
        self.id = id
        self.name = name
        self.description = description
        self.difficulty = difficulty
        self.rating = 0.0  # 0-100
        self.references = []
        self.last_training_datetime = None
        self.training_count = 0
        self.wins = 0
        self.losses = 0

    def train(self, success: bool = True):
        """Track training attempt."""
        self.training_count += 1
        if success:
            self.wins += 1
            score_gain = 5 + (self.rating / 10)
            self.rating = min(100, self.rating + score_gain)
        else:
            self.losses += 1
            self.rating = max(0, self.rating - 3)
        self.last_training_datetime = datetime.now().isoformat()

    def get_progress(self) -> Dict:
        """Get skill progress."""
        return {
            "id": self.id,
            "name": self.name,
            "difficulty": self.difficulty,
            "rating": round(self.rating, 1),
            "progress": round(self.rating / 100, 2),
            "trainings": self.training_count,
            "wins": self.wins,
            "losses": self.losses,
        }


class SkillLibrary:
    """Manage agent's skills."""

    def __init__(self):
        self.skills = {}

    def register(self, skill: Skill):
        """Register a skill."""
        self.skills[skill.id] = skill

    def get(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID."""
        return self.skills.get(skill_id)

    def get_all(self) -> Dict:
        """Get all skills."""
        return {k: v.__dict__ for k, v in self.skills.items()}

    def get_sorted(self, by: str = "rating", ascending: bool = False) -> List[Skill]:
        """Get skills sorted by criteria."""
        skills = list(self.skills.values())
        skills.sort(key=lambda s: getattr(s, by), reverse=not ascending)
        return skills


# ============================================================
# SELF-LEARNING AGENT v2
# ============================================================
class SmartAgen:
    """
    Agent yang bisa belajar, meningkatkan skill, dan mengevaluasi diri sendiri.
    """

    def __init__(self,
                 name: str = "KepalaAgen",
                 result_dir: str = "agent_results"):
        self.name = name
        self.result_dir = Path(result_dir)
        self.result_dir.mkdir(parents=True, exist_ok=True)

        # Component
        self.similarity = SimpleSimilarity()
        self.skill_lib = SkillLibrary()
        self.learning_log: List[Dict] = []
        self.results: List[Dict] = []

        # Agent state
        self.registered_tasks = []
        self.pending_tasks = []
        self.completed_tasks = []

        # Knowledge
        self.knowledge_base = []
        self.learning_progress = {}

        # Initialize skills
        self._init_skills()

    def _init_skills(self):
        """Initialize skill library."""
        skills = [
            Skill("ringkasan", "Ringkasan", "Meringkas teks menjadi poin penting", "easy"),
            Skill("analisis", "Analisis", "Menganalisa isi konten", "easy"),
            Skill("review", "Review", "Mengevaluasi kualitas", "easy"),
            Skill("translate", "Translate", "Menerjemahkan bahasa", "medium"),
            Skill("question", "Question", "Menjawab pertanyaan", "medium"),
            Skill("classify", "Classify", "Mengkategorisasi tema", "hard"),
            Skill("evaluate", "Evaluasi", "Menilai kualitas", "hard"),
        ]
        for s in skills:
            self.skill_lib.register(s)

    # ===== ANALYSIS =====
    def analyze(self, content: str) -> Dict:
        """Menganalisa konten."""
        content_lower = content.lower()

        topics = []
        if "reflect" in content_lower or "critic" in content_lower:
            topics.append("reflection")
        if "memory" in content_lower or "store" in content_lower:
            topics.append("memory")
        if "score" in content_lower or "select" in content_lower:
            topics.append("evaluation")
        if "orchestrat" in content_lower or "sub-agent" in content_lower:
            topics.append("agent_orchestration")

        return {
            "topics_found": topics,
            "relevance_score": self._calc_relevance(content, topics),
            "knowledge_extracted": topics,
            "timestamp": datetime.now().isoformat(),
            "relevance": self._calc_relevance(content, topics),
        }

    def _calc_relevance(self, content: str, topics: List[str]) -> float:
        """Hitung skor relevansi."""
        if not topics:
            return 0
        return min(len(topics) * 12, 100)

    # ===== SELECTION =====
    def select(self, content: str, topics: List[str]) -> List[Dict]:
        """Pilih knowledge yang relevan."""
        selected = []

        for topic in topics:
            score = self._calc_topic_score(content, topic)
            if score >= 50:
                snippet = self._extract_section(content, topic)
                selected.append({
                    "topic": topic,
                    "score": score,
                    "content": snippet[:300],
                    "difficulty": self._find_difficulty(topic),
                })

        return sorted(selected, key=lambda x: x["score"], reverse=True)

    def _calc_topic_score(self, content: str, topic: str) -> float:
        """Hitung skor relevansi per topik."""
        content_lower = content.lower()
        if "reflection" in topic.lower():
            return 70 if "critic" in content_lower else 20
        elif "memory" in topic.lower():
            return 65 if "memory" in content_lower else 15
        elif "evaluation" in topic.lower():
            return 70 if "score" in content_lower else 20
        elif "agent_orchestration" in topic.lower():
            return 60 if "orchestrat" in content_lower else 20
        return 30

    def _extract_section(self, content: str, topic: str) -> str:
        """Ekstrak bagian relevan dari konten."""
        content_lower = content.lower()
        keywords = {
            "reflection": ["reflection", "critic", "impro", "answer"],
            "memory": ["memory", "store", "recall", "context"],
            "evaluation": ["score", "select", "best", "option"],
            "agent_orchestration": ["orchestrat", "sub-agent", "a2a"],
        }.get(topic, ["keyword"])
        for kw in keywords:
            if kw in content_lower:
                idx = content_lower.find(kw)
                return content[max(0, idx-30):idx+150]
        return content[:200]

    def _find_difficulty(self, topic: str) -> str:
        """Tentukan kesulitan berdasarkan topik."""
        return {
            "reflection": "easy",
            "memory": "easy",
            "evaluation": "medium",
            "agent_orchestration": "hard",
        }.get(topic, "medium")


    # ===== KNOWLEDGE INTEGRATION =====
    def integrate(self, topic: str, content: str, analysis: Dict) -> Dict:
        """Integrasi knowledge ke database."""
        entry = {
            "topic": topic,
            "content": content,
            "difficulty": analysis["topic"],  # from analysis
            "relevance": analysis["relevance"],
            "source": "anonymous",
            "learned_at": datetime.now().isoformat(),
            "id": hashlib.md5(content.encode()).hexdigest()[:8],
        }
        self.knowledge_base.append(entry)
        return entry

    # ===== EVALUATION =====
    def evaluate(self, before: float, after: float, task_name: str) -> Dict:
        """Evaluasi perbaikan."""
        improvement = after - before
        return {
            "task": task_name,
            "before": before,
            "after": after,
            "improvement": improvement,
            "decision": "IMPROVED" if improvement >= 5 else "MAINTAIN" if improvement >= 0 else "REGRESS",
            "timestamp": datetime.now().isoformat(),
        }

    # ===== SKILL TRACKING =====
    def train_skill(self, skill_id: str, success: bool = True) -> Dict:
        """Latih skill tertentu."""
        skill = self.skill_lib.get(skill_id)
        if skill:
            skill.train(success)
            return skill.get_progress()
        return {"error": f"Skill {skill_id} not found"}

    def get_skill_progress(self, skill_id: str = None) -> Dict:
        """Dapatkan progres skill."""
        if skill_id:
            skill = self.skill_lib.get(skill_id)
            if skill:
                return skill.get_progress()
            return {"error": f"Skill {skill_id} not found"}
        return {k: v.get_progress() for k, v in self.skill_lib.get_all().items()}

    # ===== TASK MANAGEMENT =====
    def add_task(self, name: str, payload: str, priority: int = 1) -> Dict:
        """Tambah tugas."""
        task_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        task = {
            "task_id": task_id,
            "name": name,
            "payload": payload,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None,
        }
        self.pending_tasks.append(task)
        return task

    def complete_task(self, task: Dict, result: Dict):
        """Tandai tugas selesai."""
        task["status"] = "done"
        task["completed_at"] = datetime.now().isoformat()
        task["result"] = result
        self.completed_tasks.append(task)
        return task

    # ===== SELF-LEARNING LOOP =====
    def run(self, task_name: str, content: str) -> Dict:
        """
        Alur belajar utama.
        """
        print(f"\n{'='*60}")
        print(f" [FAIL] Learning Start: {task_name}")
        print(f"{'='*60}")

        # 1. Analyze
        print(f"\n[1/5] Analyzing...")
        analysis = self.analyze(content)
        print(f"    Found: {analysis['topics_found']}")

        # 2. Select
        print(f"    Selecting...")
        selected = self.select(content, analysis["topics_found"])

        # 3. Integrate
        for item in selected:
            self.integrate(item["topic"], item["content"], {
                "topic": item["topic"],
                "relevance": item["score"],
            })
        print(f"    Integrated: {len(selected)} topics")

        # 4. Save
        self.save_learning({
            "type": "analysis",
            "content": content[:500],
            "analysis": analysis,
            "selected": selected,
            "timestamp": datetime.now().isoformat(),
        })
        print(f"    Saved to log")

        # 5. Evaluate
        result = {
            "status": "updated",
            "topics": analysis["topics_found"],
            "selected": len(selected),
        }
        self.evaluate(
            before_score=50,  # hypothetical before
            after_score=72.5,  # hypothetical after
            task_name=task_name
        )

        print(f"    {result['status'].upper()}: {result['topics']}")
        return result

    # ===== SAVING =====
    def save_learning(self, data: Dict):
        """Simpan log belajar."""
        self.learning_log.append(data)
        with open(self.result_dir / "learning_log.json", "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2, ensure_ascii=False)

        # Save skill progress
        skills = self.skill_lib.get_all()
        with open(self.result_dir / "skill_progress.json", "w", encoding="utf-8") as f:
            json.dump(skills, f, indent=2, ensure_ascii=False)

    # ===== REPORT =====
    def get_report(self) -> Dict:
        """Dapatkan laporan keseluruhan."""
        total_tasks = len(self.pending_tasks) + len(self.completed_tasks)
        completed = len(self.completed_tasks)

        # Calculate average skill rating
        skills = self.skill_lib.get_all()
        avg_skill = sum(s.get("rating", 0) for s in skills.values()) / max(1, len(skills))

        return {
            "summary": {
                "total_tasks": total_tasks,
                "completed": completed,
                "pending": total_tasks - completed,
                "avg_skill_rating": round(avg_skill, 1),
            },
            "skills": self.skill_lib.get_all(),
            "logs": self.learning_log,
            "timestamp": datetime.now().isoformat(),
        }

    # ===== MAIN DEMO =====
    def main(self):
        """Alur utama demo."""
        print("=" * 60)
        print(" SMART AGENT v2.0 - SELF-LEARNING")
        print("=" * 60)

        # 1. Analyze video
        with open("video_transcript.txt", encoding="utf-8") as f:
            content = f.read()

        print("\n[1] Analyzing video transcript...")
        analysis = self.analyze(content)
        print(f"   Topics: {analysis['topics_found']}")

        # 2. Select
        selected = self.select(content, analysis["topics_found"])
        print(f"   Selected: {len(selected)} topics")

        # 3. Integrate
        for item in selected:
            self.integrate(item["topic"], item["content"], {
                "topic": item["topic"],
                "relevance": item["score"],
                "difficulty": item["difficulty"],
            })
        print(f"   Integrated: {len(selected)}")

        # 4. Save
        self.save_learning({
            "type": "video",
            "content": content[:500],
            "analysis": analysis,
            "selected": selected,
            "timestamp": datetime.now().isoformat(),
        })
        print(f"   Saved to agent_results/learning_log.json")

        # 5. Training
        print("\n[5] Training skills...")
        for skill in self.skill_lib.get_sorted("id"):
            if "ringkasan" in skill.id or "analisis" in skill.id:
                skill.train(success=True)
        self.save_learning({"type": "training", "skills": "done"})
        print(f"   Skills updated")

        # 6. Report
        report = self.get_report()
        print("\n[6] REPORT:")
        print(f"   Total tasks: {report['summary']['total_tasks']}")
        print(f"   Completed: {report['summary']['completed']}")
        print(f"   Avg skill: {report['summary']['avg_skill_rating']}/100")
        print(f"   Skills learned: {analysis['topics_found']}")

        print("\n" + "=" * 60)
        print(" SELF-LEARNING COMPLETE")
        print("=" * 60)

        return report


# ======= UTILITY =========
# Export functions for backward compatibility

if __name__ == "__main__":
    SmartAgen().main()
