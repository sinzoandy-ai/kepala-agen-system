#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART AGENT v3.1 - IMPROVED
===================================
Improvements:
- Better semantic similarity (TF-IDF inspired)
- Better memory (weighted recent + historical)
- Better evaluation (more criteria)
- Better skill training (adaptive)
- More data points for evaluation

CARA GUNA:
>>> from smart_agen_v3_1 import SmartAgent
>>> agen = SmartAgent()
>>> agen.learn_from_source('video', transcript)
>>> agen.train_from_data(more_data)
>>> agen.evaluate_and_report()
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
# ADVANCED EMBEDDINGS (TF-IDF)
# ============================================================
class TFIDFEmbedding:
    """
    TF-IDF inspired embedding for better semantic similarity.
    """

    def __init__(self):
        self.word_freq = {}
        self.word_idf = {}
        self.word_index = 0
        self.doc_count = 0

    def build_vocab(self, texts: List[str], doc_freq=False):
        """Build vocabulary with TF-IDF weights."""
        self.doc_count = len(texts)
        self.word_freq = {}

        for text in texts:
            # Count word frequency
            word_counts = {}
            for word in text.lower().split():
                word = word.strip(".,!?()[]{}'\"-:;")
                if word and len(word) > 1:
                    word_counts[word] = word_counts.get(word, 0) + 1

            for word, count in word_counts.items():
                if word not in self.word_freq:
                    self.word_freq[word] = []
                self.word_freq[word].append(count)

        # Calculate IDF (Inverse Document Frequency)
        for word, counts in self.word_freq.items():
            # How many docs contain this word
            docs_with = sum(1 for c in counts if c > 0)
            self.word_idf[word] = 1.0 + (self.doc_count / max(1, docs_with))

    def text_to_vector(self, text: str) -> Dict[str, float]:
        """Convert text to TF-IDF weighted vector."""
        word_counts = {}
        for word in text.lower().split():
            word = word.strip(".,!?()[]{}'\"-:;")
            if word and len(word) > 1:
                word_counts[word] = word_counts.get(word, 0) + 1

        tfidf_vector = {}
        for word, count in word_counts.items():
            if word in self.word_idf:
                tf = count / (sum(word_counts.values()) + 1e-6)
                idf = self.word_idf[word]
                tfidf_vector[word] = tf * idf
        return tfidf_vector

    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two TF-IDF vectors."""
        # Find common words
        common = set(vec1.keys()) & set(vec2.keys())
        if not common:
            return 0.0

        dot_product = sum(vec1[w] * vec2[w] for w in common)
        norm1 = sum(v * v for v in vec1.values()) ** 0.5
        norm2 = sum(v * v for v in vec2.values()) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        self.build_vocab([text1, text2])
        vec1 = self.text_to_vector(text1)
        vec2 = self.text_to_vector(text2)
        return self.cosine_similarity(vec1, vec2)


# ============================================================
# IMPROVED SHORT-TERM MEMORY
# ============================================================
class WeightedMemory:
    """
    Weighted memory buffer with recent + historical.
    """

    def __init__(self, max_recent: int = 5, max_total: int = 50):
        self.max_recent = max_recent
        self.max_total = max_total
        self.recent_buffer = []  # Most recent
        self.history = []  # All interactions

    def add(self, content: str, context: str = ""):
        """Add to memory with weighting."""
        entry = {
            'content': content[:200],
            'context': context,
            'timestamp': datetime.now().isoformat(),
        }
        self.recent_buffer.append(entry)
        self.history.append(entry)

        # Keep recent buffer limited
        if len(self.recent_buffer) > self.max_recent:
            self.recent_buffer.pop(0)

        # Keep history limited
        if len(self.history) > self.max_total:
            self.history.pop(0)

    def get_recent(self, n: int = 3) -> List[Dict]:
        """Get most recent items."""
        return self.recent_buffer[-n:]

    def get_all(self) -> List[Dict]:
        """Get all memory items."""
        return self.history

    def get_similar(self, query: str, similarity: TFIDFEmbedding, top_n: int = 3) -> List[Tuple[str, float]]:
        """Find similar memories."""
        if not self.history:
            return []

        query_vec = similarity.text_to_vector(query)
        results = []

        for item in self.history:
            item_vec = similarity.text_to_vector(item['content'])
            score = similarity.cosine_similarity(query_vec, item_vec)
            if score > 0.05:
                results.append((item['content'], score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]


# ============================================================
# IMPROVED EVALUATOR
# ============================================================
class SmartEvaluator:
    """
    Improved evaluator with more criteria and adaptive scoring.
    """

    def __init__(self):
        self.results = []
        self.criteria_weights = {
            'quality': 0.35,
            'completeness': 0.25,
            'accuracy': 0.20,
            'efficiency': 0.10,
            'relevance': 0.10,
        }

    def score(self, content: str, task_type: str, reference: str = None) -> Dict:
        """
        Score output based on multiple criteria.
        """
        # Calculate base scores
        q_score = self._score_quality(content, task_type)
        c_score = self._score_completeness(content, task_type, reference)
        a_score = self._score_accuracy(content, reference)
        e_score = self._score_efficiency(content)
        r_score = self._score_relevance(content, task_type)

        # Weighted total
        total = (
            q_score * self.criteria_weights['quality'] +
            c_score * self.criteria_weights['completeness'] +
            a_score * self.criteria_weights['accuracy'] +
            e_score * self.criteria_weights['efficiency'] +
            r_score * self.criteria_weights['relevance']
        )

        breakdown = {
            'quality': round(q_score, 1),
            'completeness': round(c_score, 1),
            'accuracy': round(a_score, 1),
            'efficiency': round(e_score, 1),
            'relevance': round(r_score, 1),
        }

        decision = self._decide(total)

        return {
            'total': round(total, 1),
            'breakdown': breakdown,
            'decision': decision,
            'timestamp': datetime.now().isoformat(),
        }

    def _score_quality(self, content: str, task_type: str) -> float:
        """Quality score (0-100)."""
        length = len(content)
        if length < 20:
            return 20
        elif length < 100:
            return 50
        elif length < 300:
            return 70
        elif length < 500:
            return 85
        else:
            return 95

    def _score_completeness(self, content: str, task_type: str, reference: str = None) -> float:
        """Completeness score (0-100)."""
        # Check for key elements
        content_lower = content.lower()

        if task_type == 'summary':
            if 'ringkasan' in content_lower or 'poin' in content_lower:
                return 70
            elif len(content) > 100:
                return 60
            else:
                return 40

        elif task_type == 'analysis':
            if 'hasil' in content_lower or 'temuan' in content_lower:
                return 75
            elif 'kategori' in content_lower or 'keengganan' in content_lower:
                return 70
            else:
                return 50

        elif task_type == 'review':
            if 'kritik' in content_lower or 'saran' in content_lower or 'kesimpulan' in content_lower:
                return 75
            elif 'kelebihan' in content_lower or 'kekurangan' in content_lower:
                return 65
            else:
                return 50

        else:
            # Default completeness
            if len(content) > 150:
                return 70
            elif len(content) > 80:
                return 60
            else:
                return 40

    def _score_accuracy(self, content: str, reference: str = None) -> float:
        """Accuracy score (0-100)."""
        # Manual scoring based on content markers
        markers = ['factual', 'correct', 'verified', 'confirmed', 'accurate']
        count = sum(1 for m in markers if m in content.lower())
        return min(100, 50 + (count * 7))

    def _score_efficiency(self, content: str) -> float:
        """Efficiency score (0-100)."""
        length = len(content)
        # Longer content = more thorough but slower
        if length > 1000:
            return 50  # Too long
        elif length > 500:
            return 60  # Long
        elif length > 200:
            return 75  # Good balance
        else:
            return 85  # Concise

    def _score_relevance(self, content: str, task_type: str) -> float:
        """Relevance score (0-100)."""
        relevant_keywords = {
            'summary': ['ringkasan', 'poin', 'keluaran', 'ringkasan'],
            'analysis': ['analisis', 'hasil', 'temuan', 'kategori'],
            'review': ['kritik', 'saran', 'kesimpulan', 'ulasan'],
            'evaluation': ['skor', 'nilai', 'penilaian', 'evaluasi'],
        }

        keywords = relevant_keywords.get(task_type, [])
        if not keywords:
            return 50

        matches = sum(1 for kw in keywords if kw in content.lower())
        return min(100, (matches / len(keywords)) * 80 + 20)

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
# IMPROVED SKILL TRAINING
# ============================================================
class AdaptiveSkillTrainer:
    """
    Adaptive skill trainer with difficulty-based learning.
    """

    def __init__(self):
        self.difficulty_factors = {
            'easy': 1.0,
            'medium': 0.7,
            'hard': 0.5,
        }

    def train(self, current_rating: float, difficulty: str, success: bool, training_rounds: int = 1) -> float:
        """
        Train skill with adaptive learning.
        """
        factor = self.difficulty_factors.get(difficulty, 1.0)

        if success:
            # Growth based on current rating and difficulty
            growth = min(10, (100 - current_rating) * 0.15 * factor)
            new_rating = min(100, current_rating + growth)
        else:
            # Decay based on difficulty
            decay = max(0, current_rating * 0.03 * factor)
            new_rating = max(0, current_rating - decay)

        return round(new_rating, 1)

    def get_progress(self, current: float, target: float, difficulty: str) -> Dict:
        """Get skill progress information."""
        gap = target - current
        return {
            'current': current,
            'target': target,
            'gap': gap,
            'percent_complete': round((current / target) * 100, 1),
            'difficulty': difficulty,
            'improvement_rate': 'high' if gap > 30 else 'medium' if gap > 15 else 'low',
        }


# ============================================================
# SMART AGENT v3.1
# ============================================================
class SmartAgentV31:
    """
    Enhanced agent with TF-IDF embeddings, weighted memory,
    and adaptive training.
    """

    def __init__(self, name: str = "KepalaAgen", result_dir: str = "agent_results"):
        self.name = name
        self.result_dir = Path(result_dir)
        self.result_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.embedder = TFIDFEmbedding()
        self.memory = WeightedMemory(max_recent=5, max_total=50)
        self.evaluator = SmartEvaluator()
        self.trainer = AdaptiveSkillTrainer()

        # Data
        self.knowledge_base = []
        self.learning_log = []
        self.results = []

        # Skills
        self.skills = {
            'ringkasan': {'rating': 42.0, 'difficulty': 'easy', 'training': 5},
            'analisis': {'rating': 38.0, 'difficulty': 'easy', 'training': 4},
            'review': {'rating': 54.0, 'difficulty': 'easy', 'training': 6},
            'translate': {'rating': 40.0, 'difficulty': 'medium', 'training': 3},
            'question': {'rating': 42.0, 'difficulty': 'medium', 'training': 4},
            'classify': {'rating': 28.0, 'difficulty': 'hard', 'training': 2},
            'evaluate': {'rating': 43.0, 'difficulty': 'hard', 'training': 4},
        }

        # Targets
        self.targets = {
            'ringkasan': 60, 'analisis': 60, 'review': 60,
            'translate': 50, 'question': 50, 'classify': 40, 'evaluate': 60
        }

        # Build vocabulary from existing knowledge
        self._build_vocab()

    def _build_vocab(self):
        """Build vocabulary from knowledge base and text files."""
        texts = []
        try:
            with open('video_transcript.txt', encoding='utf-8') as f:
                texts.append(f.read())
        except:
            pass
        try:
            with open('video_transcript2.txt', encoding='utf-8') as f:
                texts.append(f.read())
        except:
            pass

        # Add knowledge base
        for k in self.knowledge_base:
            if k.get('content'):
                texts.append(k['content'])

        # Add skill descriptions
        skill_descriptions = [
            'ringkasan teks ringkasan poin',
            'analisis data analisis temuan',
            'review kualitas review kritis',
            'translate bahasa terjemahan',
            'question pertanyaan jawab',
            'classify kategori klasifikasi',
            'evaluate penilaian evaluasi',
        ]
        texts.extend(skill_descriptions)

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

        # 5. Evaluate
        result = self._evaluate(content, task_type=source_type)
        print(f"[{'5':>2}] Evaluated: {result['decision']}/{result['total']}")

        # Save
        self.save_progress()
        self.learning_log.append({
            'type': 'learning',
            'source': source_type,
            'topics': analysis['topics_found'],
            'selected': len(selected),
            'evaluation': result,
        })

        return {
            'status': 'learning_complete',
            'topics': analysis['topics_found'],
            'selected': len(selected),
            'evaluation': result,
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
            "relevance_score": len(topics) * 12,
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
        return self.evaluator.score(content, task_type)

    def train_skill(self, skill_id: str, success: bool = True):
        """Train a skill with adaptive learning."""
        if skill_id in self.skills:
            current = self.skills[skill_id]['rating']
            difficulty = self.skills[skill_id]['difficulty']
            target = self.targets.get(skill_id, 60)

            new_rating = self.trainer.train(
                current_rating=current,
                difficulty=difficulty,
                success=success
            )

            self.skills[skill_id]['rating'] = new_rating
            self.skills[skill_id]['training'] += 1

            # Update target if rating exceeds
            if new_rating >= target:
                self.targets[skill_id] = round(new_rating + 10)

    def get_report(self) -> Dict:
        """Get full report."""
        avg_skill = sum(s['rating'] for s in self.skills.values()) / max(1, len(self.skills))

        # Get most recent evaluation
        recent_evals = [r for r in self.learning_log if 'evaluation' in r]
        avg_eval = 0
        if recent_evals:
            avg_eval = sum(r['evaluation']['total'] for r in recent_evals) / len(recent_evals)

        # Get most recent evaluation
        recent_eval = recent_evals[-1] if recent_evals else None

        return {
            "summary": {
                "total_tasks": len(self.learning_log),
                "avg_skill_rating": round(avg_skill, 1),
                "avg_evaluation": round(avg_eval, 1),
                "knowledge_count": len(self.knowledge_base),
            },
            "skills": self.skills,
            "learning_log": self.learning_log,
            "knowledge_base": self.knowledge_base,
            "timestamp": datetime.now().isoformat(),
        }

    def save_progress(self):
        """Save all progress."""
        with open(self.result_dir / "learning_log.json", "w", encoding="utf-8") as f:
            json.dump(self.learning_log, f, indent=2, ensure_ascii=False)

        with open(self.result_dir / "knowledge_base.json", "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

        with open(self.result_dir / "skill_progress.json", "w", encoding="utf-8") as f:
            json.dump(self.skills, f, indent=2, ensure_ascii=False)

    def test_with_video(self, video_file: str = "video_transcript.txt"):
        """Test with video transcript."""
        print("\n" + "=" * 60)
        print(" TESTING WITH VIDEO TRANSCRIPT")
        print("=" * 60)

        with open(video_file, encoding="utf-8") as f:
            content = f.read()

        # Learn
        result = self.learn_from_source("video", content)

        # Report
        report = self.get_report()

        print("\n" + "=" * 60)
        print(" REPORT")
        print("=" * 60)
        print(f"   Topics: {result['topics']}")
        print(f"   Selected: {result['selected']}")
        print(f"   Evaluation: {result['evaluation']['decision']} / {result['evaluation']['total']}")
        print(f"   Average skill: {report['summary']['avg_skill_rating']:.1f} / 100")
        print(f"   Average eval: {report['summary']['avg_evaluation']:.1f} / 100")
        print(f"   Knowledge stored: {report['summary']['knowledge_count']}")
        print("=" * 60)

        return report


# ======= TEST =======
if __name__ == "__main__":
    agent = SmartAgentV31()
    agent.test_with_video()
