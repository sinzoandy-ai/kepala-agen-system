#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART AGENT v3.0 - SEMANTIC SEARCH + MEMORY + EVALUATION
========================================================
Dengan:
- Cosine similarity-based semantic search
- Short-term memory buffer
- Auto-evaluation framework
- Skill tracking & self-improvement loop

CARA GUNA:
>>> from smart_agen_v3 import SmartAgent
>>> agen = SmartAgent()
>>> agen.learn_from_source("video", transcript)
>>> agen.evaluate_and_improve()
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
# SIMPLE EMBEDDINGS (Word Frequency)
# ============================================================
class SimpleEmbedding:
    """
    Simple word-frequency vectorizer.
    (For real usage: swap with sentence-transformers or OpenAI API)
    """

    def __init__(self):
        self.vocab = {}
        self.word_index = 0

    def build_vocab(self, texts: List[str]):
        """Build vocabulary from texts."""
        for text in texts:
            self._add_text(text)

    def _add_text(self, text: str):
        for word in text.lower().split():
            word = word.strip(".,!?()[]{}'\"-:;")
            if word and len(word) > 1:
                if word not in self.vocab:
                    self.vocab[word] = self.word_index
                    self.word_index += 1

    def text_to_vector(self, text: str) -> List[Optional[int]]:
        """Convert text to vector (0 if word not in vocab)."""
        vector = [0] * len(self.vocab)
        for word in text.lower().split():
            word = word.strip(".,!?()[]{}'\"-:;")
            if word in self.vocab:
                vector[self.vocab[word]] += 1
        return vector

    def cosine_similarity(self, vec1: List[Optional[int]], vec2: List[Optional[int]]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2) if a and b)
        norm1 = (sum(a * a for a in vec1)) ** 0.5
        norm2 = (sum(b * b for b in vec2)) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def embed(self, text: str) -> List[Optional[int]]:
        """Get embedding vector for text."""
        return self.text_to_vector(text)


# ============================================================
# SHORT-TERM MEMORY
# ============================================================
class ShortTermMemory:
    """
    Short-term memory buffer for recent interactions.
    """

    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.buffer = []
        self.history = []

    def add(self, content: str, context: str = ""):
        """Add to memory buffer."""
        self.buffer.append({
            "content": content[:200],
            "context": context,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)

    def get_recent(self, n: int = 5) -> List[Dict]:
        """Get recent memories."""
        return self.buffer[-n:]

    def add_to_history(self, entry: Dict):
        """Add to history log."""
        self.history.append({
            **entry,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.history) > 100:
            self.history.pop(0)

    def get_relevant(self, query: str, similarity: SimpleEmbedding,
                     top_n: int = 3) -> List[Tuple[str, float]]:
        """Find relevant memories based on query."""
        if not self.buffer:
            return []

        query_vec = similarity.text_to_vector(query)
        results = []

        for item in self.buffer:
            item_vec = similarity.text_to_vector(item["content"])
            score = similarity.cosine_similarity(query_vec, item_vec)
            if score > 0.1:
                results.append((item["content"], score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]


# ============================================================
# EVALUATION FRAMEWORK
# ============================================================
class Evaluator:
    """
    Evaluasi output berdasarkan multiple criteria.
    """

    def __init__(self):
        self.results = []
        self.criteria = {
            "quality": 0.40,      # Kualitas umum
            "speed": 0.25,        # Efisiensi
            "completeness": 0.20,  # Kelengkapan
            "accuracy": 0.15,     # Akurasi
        }

    def score(self, content: str, task_type: str, skill_level: str = "medium") -> Dict:
        """
        Score output based on criteria.
        """
        score = 0.0
        breakdown = {}

        # Quality score (40%)
        q_score = self._score_quality(content, task_type)
        score += q_score * self.criteria["quality"]
        breakdown["quality"] = round(q_score, 1)

        # Speed score (25%)
        s_score = self._score_speed(content, task_type)
        score += s_score * self.criteria["speed"]
        breakdown["efficiency"] = round(s_score, 1)

        # Completeness score (20%)
        c_score = self._score_completeness(content, task_type)
        score += c_score * self.criteria["completeness"]
        breakdown["completeness"] = round(c_score, 1)

        # Accuracy score (15%)
        a_score = self._score_accuracy(content)
        score += a_score * self.criteria["accuracy"]
        breakdown["accuracy"] = round(a_score, 1)

        total = round(score, 1)
        decision = self._decide(total)

        return {
            "total": total,
            "breakdown": breakdown,
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
        }

    def _score_quality(self, content: str, task_type: str) -> float:
        """Score quality (0-100)."""
        if not content or len(content.strip()) < 10:
            return 20

        # Length check
        if len(content) < 50:
            return 40
        elif len(content) < 200:
            return 60
        elif len(content) < 500:
            return 80
        else:
            return 90

    def _score_speed(self, content: str, task_type: str) -> float:
        """Score efficiency (0-100)."""
        # Penalty for very long output
        length = len(content)
        if length > 1000:
            return 50
        elif length > 500:
            return 65
        elif length > 200:
            return 80
        else:
            return 85

    def _score_completeness(self, content: str, task_type: str) -> float:
        """Score completeness (0-100)."""
        # Check for key markers based on task type
        if task_type == "summary":
            if "ringkasan" in content.lower() or "poin" in content.lower():
                return 70
            else:
                return 50
        elif task_type == "analysis":
            if "hasil" in content.lower() or "analisis" in content.lower():
                return 75
            else:
                return 40
        else:
            # Default completeness check
            if len(content) > 100:
                return 70
            else:
                return 40

    def _score_accuracy(self, content: str) -> float:
        """Score accuracy (0-100)."""
        # Manual scoring based on content quality
        quality_markers = ["fitur", "keuntungan", "kekurangan", "saran", "kesimpulan"]
        count = sum(1 for m in quality_markers if m.lower() in content.lower())
        return min(100, 50 + (count * 7))

    def _decide(self, score: float) -> str:
        """Decision based on score."""
        if score >= 80:
            return "POKOK"
        elif score >= 70:
            return "BAIK"
        elif score >= 60:
            return "CUKUP"
        elif score >= 50:
            return "KURANG"
        else:
            return "GAGAL"


# ============================================================
# SMART AGENT v3
# ============================================================
class SmartAgent:
    """
    Agent v3: Semantic search + memory + evaluation + self-improvement.
    """

    def __init__(self, name: str = "KepalaAgen", result_dir: str = "agent_results"):
        self.name = name
        self.result_dir = Path(result_dir)
        self.result_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.embedder = SimpleEmbedding()
        self.memory = ShortTermMemory(max_size=10)
        self.evaluator = Evaluator()

        # Data
        self.knowledge_base = []
        self.learning_log = []
        self.results = []

        # Skills
        self.skills = {
            "ringkasan": {"rating": 0.0, "difficulty": "easy", "training": 0},
            "analisis": {"rating": 0.0, "difficulty": "easy", "training": 0},
            "review": {"rating": 0.0, "difficulty": "easy", "training": 0},
            "translate": {"rating": 0.0, "difficulty": "medium", "training": 0},
            "question": {"rating": 0.0, "difficulty": "medium", "training": 0},
            "classify": {"rating": 0.0, "difficulty": "hard", "training": 0},
            "evaluate": {"rating": 0.0, "difficulty": "hard", "training": 0},
        }

        # Build vocabulary
        self._build_vocab()

    def _build_vocab(self):
        """Build vocabulary from knowledge base."""
        texts = [k["content"] for k in self.knowledge_base if k.get("content")]
        texts.append("ringkasan analisis review translate question classolove evaluate")
        self.embedder.build_vocab(texts)

    def learn_from_source(self, source_type: str, content: str) -> Dict:
        """
        Main learning loop.
        """
        print(f"\n{'='*60}")
        print(f" LEARNING: {source_type}")
        print(f"{'='*60}")

        # 1. Analyze
        analysis = self._analyze(content)
        print(f"[{'1':>2}] Analyzed: {analysis['topics_found']}")

        # 2. Select
        selected = self._select(content, analysis["topics_found"])
        print(f"[{'2':>2}] Selected: {len(selected)} topics")

        # 3. Integrate
        for item in selected:
            self._integrate(item, analysis)
        print(f"[{'3':>2}] Integrated: {len(selected)}")

        # 4. Store in memory
        self.memory.add(content, source_type)
        self._save_progress()

        # 5. Evaluate
        result = self._evaluate(content, task_type=source_type)
        print(f"[{'5':>2}] Evaluated: {result['decision']}/{result['total']}")

        return {
            "status": "learning_complete",
            "topics": analysis["topics_found"],
            "selected": len(selected),
            "evaluation": result,
        }

    def _analyze(self, content: str) -> Dict:
        """Analyze content."""
        content_lower = content.lower()
        topics = []

        if "reflection" in content_lower or "critic" in content_lower:
            topics.append("reflection")
        if "memory" in content_lower or "store" in content_lower:
            topics.append("memory")
        if "score" in content_lower or "select" in content_lower:
            topics.append("evaluation")
        if "orchestrat" in content_lower or "sub-agent" in content_lower:
            topics.append("agent_orchestration")

        return {
            "topics_found": topics,
            "relevance_score": len(topics) * 10,
            "knowledge_extracted": topics,
            "timestamp": datetime.now().isoformat(),
        }

    def _select(self, content: str, topics: List[str]) -> List[Dict]:
        """Select relevant topics."""
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
        """Calculate topic score."""
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
        """Extract section from content."""
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
        """Find difficulty level."""
        return {
            "reflection": "easy",
            "memory": "easy",
            "evaluation": "medium",
            "agent_orchestration": "hard",
        }.get(topic, "medium")

    def _integrate(self, item: Dict, analysis: Dict):
        """Integrate knowledge."""
        entry = {
            "topic": item["topic"],
            "content": item["content"],
            "difficulty": item["difficulty"],
            "relevance": item["score"],
            "source": "video_transcript",
            "learned_at": datetime.now().isoformat(),
            "id": hashlib.md5(item["content"].encode()).hexdigest()[:8],
        }
        self.knowledge_base.append(entry)

    def _evaluate(self, content: str, task_type: str) -> Dict:
        """Evaluate output."""
        score = self.evaluator.score(content, task_type)
        skill_id = self._map_task_to_skill(task_type)
        if skill_id:
            self._train_skill(skill_id, score["total"] >= 60)

        self.learning_log.append({
            **score,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
        })

        return score

    def _train_skill(self, skill_id: str, success: bool):
        """Train skill."""
        if skill_id in self.skills:
            self.skills[skill_id]["training"] += 1
            if success:
                self.skills[skill_id]["rating"] = min(100, self.skills[skill_id]["rating"] + 3)
            else:
                self.skills[skill_id]["rating"] = max(0, self.skills[skill_id]["rating"] - 2)

    def _map_task_to_skill(self, task_type: str) -> str:
        """Map task type to skill."""
        mapping = {
            "summary": "ringkasan",
            "analysis": "analisis",
            "review": "review",
            "evaluation": "evaluate",
        }
        return mapping.get(task_type, "evaluate")

    def _save_progress(self):
        """Save progress."""
        # Save knowledge
        with open(self.result_dir / "learning_log.json", "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2, ensure_ascii=False)

        # Save knowledge base
        with open(self.result_dir / "knowledge_base.json", "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

        # Save skill progress
        with open(self.result_dir / "skill_progress.json", "w", encoding="utf-8") as f:
            json.dump(self.skills, f, indent=2, ensure_ascii=False)

    def get_report(self) -> Dict:
        """Get full report."""
        avg_skill = sum(s["rating"] for s in self.skills.values()) / max(1, len(self.skills))

        return {
            "summary": {
                "total_tasks": len(self.learning_log),
                "avg_skill_rating": round(avg_skill, 1),
                "avg_evaluation": round(sum(r["total"] for r in self.learning_log if "total" in r) / max(1, len(self.learning_log)), 1),
            },
            "skills": self.skills,
            "logs": self.learning_log,
            "knowledge_count": len(self.knowledge_base),
            "timestamp": datetime.now().isoformat(),
        }

    def test_with_video(self, video_file: str = "video_transcript.txt"):
        """Test with video transcript."""
        print("\n" + "=" * 60)
        print(" TESTING WITH VIDEO TRANSCRIPT")
        print("=" * 60)

        with open(video_file, encoding="utf-8") as f:
            content = f.read()

        # Learn
        result = self.learn_from_source("video", content)

        # Evaluate
        report = self.get_report()

        # Print summary
        print("\n" + "=" * 60)
        print(" REPORT")
        print("=" * 60)
        print(f"   Topics: {result['topics']}")
        print(f"   Selected: {result['selected']}")
        print(f"   Evaluation: {result['evaluation']['decision']} / {result['evaluation']['total']}")
        print(f"   Average skill: {report['summary']['avg_skill_rating']} / 100")
        print(f"   Average eval: {report['summary']['avg_evaluation']} / 100")
        print(f"   Knowledge stored: {report['knowledge_count']}")
        print("=" * 60)

        return report


# ======= TEST =======
if __name__ == "__main__":
    agent = SmartAgent()
    agent.test_with_video()
