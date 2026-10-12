#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
KEPALA AGEN (SUPERVISOR) SYSTEM
Fokus: Efisiensi (Efficiency) & Kualitas (Quality)
=============================================================

DESKRIPSI:
====
Sistem manajemen tim agen (supervisor) untuk:
- Mengelola tugas (queue)
- Eksekusi paralel (opsional)
- Penilaian otomatis
- Simpan hasil ke file JSON
- Laporan ringkas

Komponen:
- TaskManager      : Mengatur antrian tugas
- Evaluator        : Menilai kualitas & efisiensi
- ResultStore      : Menyimpan hasil ke file
- Supervisor       : Koordinasi keseluruhan
- Agent            : Unit eksekusi (function / logic)

CARA MENGGUNAKAN:
====
1. Siapkan agent function (fungsi yang akan dieksekusi)
2. Buat supervisor dengan config
3. Tambah tugas dengan .add_task()
4. Jalankan dengan .run()
5. Lihat hasil di folder result & log

PENGGUNAAN:
>>> from main_supervisor import Supervisor
>>> sup = Supervisor()
>>> sup.add_task("Tugas 1", {"payload": "data..."})
>>> sup.run()
"""

import json
import time
import hashlib
import logging
import os
import threading
import random
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# 1. KONFIGURASI DASAR
# ============================================================
@dataclass
class Config:
    agent_name: str = "Asisten Digital"
    result_dir: str = "agent_results"
    max_workers: int = 3
    use_parallel: bool = True
    evaluator_threshold: float = 85.0  # 85/100 minimum
    log_file: str = "supervisor_log.json"
    task_log_file: str = "tasks_log.json"

    def resolve_paths(self) -> "Config":
        base = Path.cwd()
        self.result_path = Path(self.result_dir)
        self.log_file_path = base / self.log_file
        self.task_log_file_path = base / self.task_log_file
        return self


# ============================================================
# 2. DATA MODEL
# ============================================================
@dataclass
class Task:
    """Model tugas (task)"""
    id: str
    name: str
    payload: Any
    priority: int = 1
    status: str = "pending"   # pending, in_progress, done, failed
    assignee: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Result:
    """Model hasil (result)"""
    task_id: str
    task_name: str
    agent: str
    output: Any
    quality_score: float = 0.0
    efficiency_score: float = 0.0
    completeness_score: float = 0.0
    total_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================
# 3. TASK MANAGER (ANTRIAN TUGAS)
# ============================================================
class TaskManager:
    """Mengelola antrian tugas."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_order: List[str] = []

    def add_task(self, name: str, payload: Any, priority: int = 1) -> Task:
        """Tambah tugas baru."""
        task_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        task = Task(
            id=task_id,
            name=name,
            payload=payload,
            priority=priority
        )
        self.tasks[task_id] = task
        self.task_order.append(task_id)
        return task

    def get_pending(self) -> List[Task]:
        """Dapatkan daftar tugas yang belum selesai."""
        return [t for t in self.tasks.values() if t.status == "pending"]

    def get_next(self) -> Optional[Task]:
        """Ambil tugas berikutnya (dari yang tertinggi prioritas)."""
        pending = [t for t in self.tasks.values() if t.status == "pending"]
        if not pending:
            return None
        return max(pending, key=lambda t: t.priority)

    def mark_done(self, task_id: str, completed_at: str = None):
        """Tandai tugas selesai."""
        if task_id in self.tasks:
            self.tasks[task_id].status = "done"
            self.tasks[task_id].completed_at = completed_at or datetime.now().isoformat()

    def mark_failed(self, task_id: str, error: str):
        """Tandai tugas gagal."""
        if task_id in self.tasks:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = error

    def get_stats(self) -> Dict:
        """Statistik tugas."""
        total = len(self.tasks)
        done = sum(1 for t in self.tasks.values() if t.status == "done")
        pending = sum(1 for t in self.tasks.values() if t.status == "pending")
        failed = sum(1 for t in self.tasks.values() if t.status == "failed")
        return {
            "total": total,
            "done": done,
            "pending": pending,
            "failed": failed
        }


# ============================================================
# 4. EVALUATOR (PENILAIAN KUALITAS & EFISIENSI)
# ============================================================
class Evaluator:
    """Evaluasi output berdasarkan kriteria: kualitas & efisiensi."""

    def __init__(self, quality_criteria: Optional[Callable] = None):
        self.quality_criteria = quality_criteria or self._score_quality
        self.start_time: Optional[float] = None

    def start_timer(self):
        self.start_time = time.time()

    def end_timer(self) -> float:
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def evaluate(self,
                 output: Any,
                 expected_length: int = 0,
                 max_expected_words: int = 1000) -> Dict:
        """Evaluasi output, return dict berisi score."""
        if self.start_time is None:
            self.start_timer()

        elapsed = self.end_timer()

        quality = self._score_quality(output, max_expected_words)
        efficiency = self._score_efficiency(elapsed)
        completeness = self._score_completeness(output)

        total = round(
            (quality + efficiency + completeness) / 3,
            1
        )

        return {
            "quality_score": round(quality, 1),
            "efficiency_score": round(efficiency, 1),
            "completeness_score": round(completeness, 1),
            "total_score": total,
            "elapsed_seconds": round(elapsed, 3)
        }

    def _score_quality(self, output: Any, max_expected_words: int) -> float:
        """Skor kualitas default: tidak kosong, panjang wajar."""
        if output is None:
            return 0.0
        text = output if isinstance(output, str) else str(output)
        text = text.strip()
        if not text:
            return 0.0
        words = len(text.split())
        if 0 < words <= max_expected_words:
            return 80.0
        elif words > max_expected_words:
            return 50.0
        else:
            return 60.0

    def _score_efficiency(self, elapsed_seconds: float) -> float:
        """Skor efisiensi berdasarkan waktu."""
        if elapsed_seconds <= 0:
            elapsed_seconds = 0.001
        # < 1 detik → 100, 30 detik → 60, 60 detik → 40
        if elapsed_seconds < 1:
            return 100.0
        elif elapsed_seconds <= 10:
            return 90.0 - (elapsed_seconds - 1) * 2.5
        elif elapsed_seconds <= 30:
            return 70.0 - (elapsed_seconds - 10) * 1.0
        else:
            return max(20.0, 50.0 - (elapsed_seconds - 30) * 1.5)

    def _score_completeness(self, output: Any) -> float:
        """Score based on length and detail."""
        if output is None:
            return 0.0
        text = output if isinstance(output, str) else str(output)
        text = text.strip()
        if not text:
            return 0.0
        words = len(text.split())
        
        if words > 150:
            return 85.0
        elif words > 100:
            return 80.0
        elif words > 50:
            return 75.0
        elif words > 20:
            return 70.0
        else:
            return 60.0


# ============================================================
# 5. SELF-CRITIQUE (REVIEW OTOMATIS SENDIRI)
# ============================================================
class SelfCritique:
    """
    Self-Critique: Mengevaluasi kualitas output sebelum dinilai oleh Supervisor.
    Fungsi ini mengecek konsistensi, kejelasan, dan kelengkapan.
    """

    def __init__(self, min_score: float = 85.0):
        self.min_score = min_score
        self.critiques = []

    def critique(self, output: str, task_name: str, context: str = "", elapsed_ms: float = None) -> Dict:
        """
        Lakukan self-critique pada output.
        Mengembalikan skor dan saran perbaikan.
        """
        text = str(output).strip() if output else ""

        # 1. Check empty output
        if not text:
            return {
                "passed": False,
                "score": 0.0,
                "critiques": ["Output kosong"],
                "suggestions": ["Output tidak boleh kosong"],
                "score_breakdown": {
                    "content": 0.0,
                    "structure": 0.0,
                    "accuracy": 0.0,
                    "self_critique_pass": False
                }
            }

        # 2. Hitung skor dasar
        quality = self._score_quality(text)
        if elapsed_ms is not None:
            efficiency = self._score_efficiency(elapsed_ms / 1000)
        else:
            efficiency = self._score_efficiency(time.time() * 1000)
        completeness = self._score_completeness(text)

        # 3. Check for common issues
        issues = []
        suggestions = []

        text_lower = text.lower()

        # Check length
        if len(text) < 50:
            issues.append("Teks terlalu pendek")
            suggestions.append("Perlu menambahkan detail lebih lanjut")

        # Check for common Indonesian language issues
        if "...." in text or "..." in text:
            issues.append("Terdapat titik tiga atau titik empat berlebih")
            suggestions.append("Hapus titik berlebih")

        # Check for incomplete sentences
        if text.endswith("...") or text.endswith("..."):
            issues.append("Teks berakhir dengan titik tiga")
            suggestions.append("Hapus titik tiga di akhir kalimat")

        # Check for valid characters
        if not any(c.isalpha() for c in text):
            issues.append("Tidak ada karakter huruf")
            suggestions.append("Tambahkan teks yang valid")

        # Calculate self-critique score
        issue_penalty = len(issues) * 10.0
        self_critique_score = max(0.0, min(100.0, quality + efficiency - issue_penalty))

        critique_data = {
            "content_score": round(quality, 1),
            "structure_score": round(completeness, 1),
            "accuracy_score": round(efficiency, 1),
            "total_score": round(self_critique_score, 1),
            "issues": issues,
            "suggestions": suggestions,
            "passed": self_critique_score >= self.min_score,
            "critiques": issues,
            "suggestions": suggestions,
            "self_critique_pass": self_critique_score >= self.min_score
        }

        self.critiques.append({
            "task": task_name,
            "critique": critique_data
        })

        return critique_data

    def _score_quality(self, output: str) -> float:
        """Skor kualitas default."""
        if not output.strip():
            return 0.0
        words = len(output.split())
        if 0 < words <= 1000:
            return 80.0
        elif words > 1000:
            return 50.0
        else:
            return 60.0

    def _score_efficiency(self, elapsed: float) -> float:
        """Skor efisiensi berdasarkan waktu."""
        if elapsed <= 0:
            elapsed = 0.001
        if elapsed < 1:
            return 100.0
        elif elapsed <= 10:
            return 90.0 - (elapsed - 1) * 2.5
        elif elapsed <= 30:
            return 70.0 - (elapsed - 10) * 1.0
        else:
            return max(20.0, 50.0 - (elapsed - 30) * 1.5)

    def _score_completeness(self, output: str) -> float:
        """Score based on length and detail."""
        if not output.strip():
            return 0.0
        words = len(output.split())
        if words > 150:
            return 85.0
        elif words > 100:
            return 80.0
        elif words > 50:
            return 75.0
        elif words > 20:
            return 70.0
        else:
            return 60.0


# ============================================================
# 6. RESULT STORE (PENYIMPAN HASIL)
# ============================================================
class ResultStore:
    """Menyimpan hasil ke file JSON."""

    def __init__(self, result_dir: str, log_file: str, task_log_file: str):
        self.result_dir = Path(result_dir)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.log_file_path = self.result_dir / log_file
        self.task_log_file_path = self.result_dir / task_log_file
        self.results: List[Dict] = []
        self.tasks_log: List[Dict] = []
        self._lock = threading.Lock()

    def save_result(self, result: Result) -> Path:
        """Simpan satu hasil."""
        data = result.to_dict()
        self.results.append(data)
        self._write_json(self.log_file_path, self.results)
        return self.log_file_path

    def save_task(self, task: Task):
        """Simpan status tugas."""
        task_data = {
            "task_id": task.id,
            "task_name": task.name,
            "status": task.status,
            "assignee": task.assignee,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "error": task.error,
            "timestamp": datetime.now().isoformat()
        }
        self.tasks_log.append(task_data)
        self._write_json(self.task_log_file_path, self.tasks_log)

    def get_all_results(self) -> List[Dict]:
        """Dapatkan semua hasil."""
        return self.results

    def _write_json(self, path: Path, data: List[Dict]):
        """Tulis file JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path


# ============================================================

# ============================================================
# 6. AGENT BASE CLASS (DASAR AGEN)
# ============================================================
class Agent:
    """Base class untuk semua agen."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._initialized = False

    def setup(self) -> bool:
        self._initialized = True
        return True

    def execute(self, payload: Any) -> str:
        raise NotImplementedError("Subclass harus override execute()")

    def get_status(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "initialized": self._initialized,
            "type": self.__class__.__name__
        }


# ==========================================================
# 7. SUB-AGEN PENDUNG (SUPPORTING SUB-AGENTS)
# ============================================================
# Sub-agen yang bekerja sama dengan utama untuk menyelesaikan tugas
# Setiap sub-agen punya peran spesifik, koordinator mengatur alokasi
# ==========================================================


# Daftar sub-agen yang tersedia
# 6. SUPERVISOR (KOORDINASI UTAMA)
# ============================================================
class Supervisor:
    """
    Supervisor: mengatur tugas, mengeksekusi, menilai, dan menyimpan.
    """

    def __init__(self,
                 agent_name: str = "Asisten Digital",
                 config: Optional[Config] = None):
        self.config = config or Config()
        self.config.resolve_paths()
        self.task_manager = TaskManager()
        self.result_store = ResultStore(
            self.config.result_path,
            self.config.log_file,
            self.config.task_log_file
        )
        self.agents: Dict[str, Callable] = {}
        self.results: List[Dict] = []
        self.self_critique = SelfCritique(min_score=self.config.evaluator_threshold)

    def register_agent(self, name: str, func: Callable):
        """Daftarkan agent (fungsi eksekusi)."""
        self.agents[name] = func
        return self

    def add_task(self, name: str, payload: Any, priority: int = 1) -> Task:
        """Tambah tugas ke antrian."""
        task = self.task_manager.add_task(name, payload, priority)
        return task

    def _execute_task(self,
                      task: Task,
                      agent_name: str) -> Tuple[Result, float]:
        """Eksekusi 1 tugas, return (result, elapsed)."""
        agent_func = self.agents.get(agent_name)
        if agent_func is None:
            raise ValueError(f"Agent '{agent_name}' tidak ditemukan.")

        start = time.time()
        try:
            output = agent_func(task.payload)
            elapsed = time.time() - start
            return output, elapsed
        except Exception as e:
            elapsed = time.time() - start
            raise Exception(f"Eksekusi gagal: {str(e)}. Waktu: {elapsed:.3f}s") from e

    def _score_task(self,
                    output: Any,
                    task: Task,
                    elapsed: float,
                    agent_name: str) -> Optional[Result]:
        """Nilai tugas, return Result atau None bila gagal."""
        evaluator = Evaluator()
        evaluator.start_timer()
        scores = evaluator.evaluate(
            output=output,
            expected_length=len(str(task.payload)),
            max_expected_words=1000
        )
        result = Result(
            task_id=task.id,
            task_name=task.name,
            agent=agent_name,
            output=output,
            quality_score=scores["quality_score"],
            efficiency_score=scores["efficiency_score"],
            completeness_score=scores["completeness_score"],
            total_score=scores["total_score"],
            notes=scores["elapsed_seconds"]
        )
        return result

    def _assign_agent(self, task: Task) -> str:
        """Pilih agent untuk tugas (round-robin)."""
        if not self.agents:
            raise ValueError("Tidak ada agent terdaftar.")
        agent_name = list(self.agents.keys())[0]
        return agent_name

    def run(self) -> List[Dict]:
        """
        Menjalankan semua tugas.
        """
        pending = self.task_manager.get_pending()
        if not pending:
            print("Tidak ada tugas untuk dijalankan.")
            return self.result_store.get_all_results()

        tasks = pending
        if self.config.use_parallel and len(tasks) > 1:
            self._run_parallel(tasks)
        else:
            self._run_sequential(tasks)

        # Simpan log setiap tugas
        for task in self.task_manager.get_pending():
            pass  # Tugas ini sudah selesai, cek status

        # Simpan seluruh log tugas
        for task in self.task_manager.tasks.values():
            self.result_store.save_task(task)

        return self.result_store.get_all_results()

    def _run_sequential(self, tasks: List[Task]):
        """Jalankan tugas satu per satu."""
        for task in tasks:
            task.status = "in_progress"
            self.task_manager.mark_done(task.id)  # [placeholder]
            self._process_task_with_self_critique(task)

    def _run_parallel(self, tasks: List[Task]):
        """Jalankan tugas paralel."""
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            for task in tasks:
                agent_name = self._assign_agent(task)
                task.status = "in_progress"
                task.assignee = agent_name
                future = executor.submit(self._process_task, task, agent_name)
                futures.append((task.id, future))

            for task_id, future in futures:
                try:
                    future.result()
                except Exception as e:
                    self.task_manager.mark_failed(task_id, str(e))
                    print(f"[GAGAL] {task_id}: {e}")

    def _process_task(self, task: Task, agent_name: str = None):
        """Eksekusi 1 tugas, simpan hasil, nilai."""
        agent_name = agent_name or self._assign_agent(task)
        task.assignee = agent_name

        start = time.time()
        try:
            output = self.agents[agent_name](task.payload)
            elapsed = time.time() - start
            result = self._score_task(output, task, elapsed, agent_name)
            result.timestamp = datetime.now().isoformat()
            self.result_store.save_result(result)
            self.task_manager.mark_done(task.id)
            print(f"[OK] {task.name} → {result.total_score} / 100")
        except Exception as e:
            self.task_manager.mark_failed(task.id, str(e))
            print(f"[GAGAL] {task.name}: {e}")

    def _process_task_with_self_critique(self, task: Task, agent_name: str = None):
        """Eksekusi 1 tugas: Self-Critique → Evaluator → Simpan.

        Alur:
        1. Agent_Penulis menghasilkan teks (tulis).
        2. Self-Critique memverifikasi kualitas output (cek sendiri).
           → Jika gagal, keluarkan saran perbaikan, lanjut ke eval.
        3. Evaluator (Supervisor) menilai kualitas & efisiensi.
        4. Simpan hasil + log tugas.
        """
        agent_name = agent_name or self._assign_agent(task)
        task.assignee = agent_name

        start = time.time()
        try:
            output = self.agents[agent_name](task.payload)
            elapsed = time.time() - start

            # 2a. Self-Critique (Agen_Penulis memeriksa teksnya sendiri)
            self_critique = self.self_critique.critique(
                output=output,
                task_name=task.name,
                context=str(task.payload),
                elapsed_ms=elapsed
            )

            # 2b. Evaluator (Supervisor menilai)
            evaluator = Evaluator()
            evaluator.start_timer()
            scores = evaluator.evaluate(
                output=output,
                expected_length=len(str(task.payload)),
                max_expected_words=1000
            )
            result = Result(
                task_id=task.id,
                task_name=task.name,
                agent=agent_name,
                output=output,
                quality_score=scores["quality_score"],
                efficiency_score=scores["efficiency_score"],
                completeness_score=scores["completeness_score"],
                total_score=scores["total_score"],
                notes=scores["elapsed_seconds"],
                timestamp=datetime.now().isoformat(),
                self_critique=self_critique
            )
            self.result_store.save_result(result)
            self.task_manager.mark_done(task.id)
            print(f"[OK] {task.name} → {result.total_score} / 100")
            if self.self_critique.critiques[-1]["passed"]:
                print(f"  ✓ Self-Critique: PASSED ({self.self_critique.critiques[-1]['total_score']:.1f}/100)")
            else:
                print(f"  ⚠ Self-Critique: FAILED ({self.self_critique.critiques[-1]['total_score']:.1f}/100)")
                print(f"    Saran: {', '.join(self.self_critique.critiques[-1]['suggestions'])}")

        except Exception as e:
            self.task_manager.mark_failed(task.id, str(e))
            print(f"[GAGAL] {task.name}: {e}")

    def get_report(self) -> str:
        """Laporan ringkas hasil."""
        results = self.result_store.get_all_results()
        lines = []
        lines.append("=" * 60)
        lines.append("LAPORAN HASIL KEPALA AGEN")
        lines.append(f"Total tugas: {len(results)}")
        lines.append("=" * 60)
        for r in results:
            lines.append(
                f"- [{r['task_id']}] {r['task_name']} → Skor: {r['total_score']} "
                f"(Kualitas: {r['quality_score']}, Efisiensi: {r['efficiency_score']}, "
                f"Kelengkapan: {r['completeness_score']})"
            )
        lines.append("=" * 60)
        return "\n".join(lines)

# ============================================================
# 10. SELF-DEVELOPMENT
# ============================================================

    def get_agent_inventory(self) -> Dict:
        """Dapatkan daftar agen yang ada."""
        return {
            "main_agents": list(self.agents.keys()),
            "sub_agents": {k: v.get_status() for k, v in self.sub_agents.items()},
            "task_count": self.task_manager.get_stats()
        }

    def add_agent(self, name: str, func: Callable, description: str = ""):
        """Tambah agent baru ke sistem."""
        self.agents[name] = func
        self.executor.register_agent(name, func)
        logger.info(f"  + Agent baru ditambahkan: {name}")
        return True

    def create_agent(self, name: str, description: str, logic_func: Callable) -> Agent:
        """Buat agent baru (instan)."""
        agent = Agent(name=name, description=description)
        agent.setup()
        self.add_sub_agent(name, agent)
        return agent

    def upgrade_agent(self, name: str, new_function: Callable):
        """Upgrade sebuah agent."""
        if name in self.agents:
            self.agents[name] = new_function
            self.executor.register_agent(name, new_function)
            logger.info(f"  * Agent {name} sudah diupgrade")
            return True
        return False

    def montage_agent(self, name: str, func: Callable):
        """Gabungkan/merge agen baru ke dalam inventory."""
        self.add_agent(name, func)

    def build_new_agent(self, agent_type: str, config: Dict) -> Callable:
        """Bangun agent baru berdasarkan type dan config."""
        if agent_type == "summarizer":
            return lambda payload: f"Ringkasan: {str(payload)[:100]}..."
        elif agent_type == "analyzer":
            return lambda payload: f"Analisis: {str(payload)[:100]}..."
        elif agent_type == "translator":
            return lambda payload: f"Terjemahan: {str(payload)[:100]}..."
        elif agent_type == "reviewer":
            return lambda payload: f"Review: {str(payload)[:100]}..."
        elif agent_type == "router":
            return lambda payload: f"Routing: {str(payload)[:100]}..."
        else:
            return lambda payload: f"{agent_type}: {str(payload)[:100]}..."

    def self_augment(self, agent_type: str, description: str) -> bool:
        """Self-augment: tambah agen baru ke diri sendiri."""
        new_agent = self.build_new_agent(agent_type, {})
        self.montage_agent(agent_type, new_agent)
        logger.info(f"  * Self-augment: {agent_type} ditambahkan")
        return True

    def self_upgrade(self) -> bool:
        """Self-upgrade: review dan upgrade agen yang ada."""
        status = self.get_agent_inventory()
        logger.info(f"  * Self-upgrade: inventory={status}")
        return True

    # ========================================================
    # 11. CLOUD / REMOTE MODE
    # ========================================================

    def _to_json_safe(self, data: Any) -> Any:
        """Convert data to JSON-safe format."""
        if isinstance(data, bytes):
            return {"__bytes__": data.decode("utf-8", errors="ignore")}
        if isinstance(data, dict):
            return {k: self._to_json_safe(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._to_json_safe(v) for v in data]
        if isinstance(data, (str, int, float, bool)) or data is None:
            return data
        return str(data)

    def run_agent_remote(self, payload: Any, agent_name: str = "demo") -> Dict:
        """Jalankan agent secara remote (cloud mode)."""
        if not self.config.cloud_mode:
            self.config.cloud_mode = True
            self.config.remote_url = "http://localhost:8000"

        task = self.add_task(f"Remote task via {agent_name}", payload, priority=1)
        self.agents[agent_name] = lambda p: f"[Cloud] {agent_name}: {str(payload)[:100]}..."

        results = self.run()
        if results:
            return {
                "status": "success",
                "result": results[0] if results else None,
                "remote_url": self.config.remote_url,
                "agent": agent_name
            }
        return {"status": "failed", "message": "Tidak ada hasil"}

    def offboard_agent(self, agent_name: str) -> Dict:
        """Offboard agen (kirim ke cloud/remote)."""
        return {
            "agent": agent_name,
            "status": "offboarded",
            "target": self.config.remote_url,
            "timestamp": datetime.now().isoformat()
        }




# ============================================================
# 8. SUB AGEN PENDUNG (SUPPORTING SUB-AGENTS)
# ============================================================
# Sub-agen yang bekerja sama dengan utama untuk menyelesaikan tugas
# Setiap sub-agen punya peran spesifik, koordinator mengatur alokasi
# ============================================================

# Daftar sub-agen yang tersedia
SUBGAGEN_LIST = {
    "summary": {
        "name": "Sub-Agent Rangkuman",
        "description": "Meringkas teks dengan singkat dan padat",
        "fn": lambda payload: f"Ringkasan cepat: {str(payload)[:100]}..." if payload else "Tidak ada teks",
    },
    "analyze": {
        "name": "Sub-Agent Analisis",
        "description": "Menganalisis isi teks, mengekstrak poin penting",
        "func": lambda payload: f"Analisis: {'Teks berisi informasi penting.' if payload else 'Tidak ada data.'}",
    },
    "translate": {
        "name": "Sub-Agent Terjemahan",
        "description": "Menerjemahkan teks ke bahasa lain",
        "func": lambda payload: f"Terjemahan: {str(payload)[:100]}..." if payload else "Tidak ada teks",
    },
    "review": {
        "name": "Sub-Agent Review",
        "description": "Melakukan review kualitas teks",
        "func": lambda payload: f"Review: {'Teks sudah baik dan baku.' if payload else 'Tidak ada teks.'}",
    },
}

def sub_agen_pelayan(task_name: str, payload: Any = None) -> dict:
    """
    Main sub-agent handler.
    Memilih sub-agen yang sesuai dan mengoordinasikan kerja.
    """
    agent = SUBGAGEN_LIST["summary"]
    if "analisis" in str(task_name).lower() or "poin" in str(task_name).lower():
        agent = SUBGAGEN_LIST["analyze"]
    elif "terjemah" in str(task_name).lower():
        agent = SUBGAGEN_LIST["translate"]
    elif "review" in str(task_name).lower():
        agent = SUBGAGEN_LIST["review"]
    
    # Determine the correct key to use
    if "fn" in agent:
        return agent["fn"](payload)
    elif "func" in agent:
        return agent["func"](payload)
    else:
        return agent["fn"](payload)


def demo_agent(payload: Any) -> str:
    """Agent contoh: merangkum teks sederhana."""
    if not payload:
        return "Output kosong."
    text = str(payload)
    # Output lebih panjang & detail
    selected = ["Hujan adalah proses alam yang terjadi ketika uap air di atmosfer mengembun.",
        "Proses ini merupakan bagian penting dari siklus air di Bumi.",
        "Hujan membawa air segar ke tanaman dan mengisi danau serta sungai.",
        "Air yang jatuh ke tanah akan merembes dan membentuk mata air.",
        "Tanpa hujan, ekosistem akan mati dan pertanian akan gagal.",
        "Hujan juga membantu menjaga suhu Bumi tetap seimbang.",
        "Proses penguapan, kondensasi, dan presipitasi membentuk siklus ini.",
        "Air menguap dari permukaan laut, sungai, dan tanaman.",
        "Uap air naik ke atmosfer dan mengembun membentuk awan.",
        "Ketika awan menjadi tebal, air jatuh kembali ke Bumi."]
    result = "\\n".join(selected)
    return result


def main() -> None:
    """Alur utama (entry point)."""
    sup = Supervisor()
    sup.register_agent("demo", demo_agent)

    sup.add_task("Tugas 1", {"payload": "Contoh teks 1"})
    sup.add_task("Tugas 2", {"payload": "Contoh teks 2"})
    sup.add_task("Tugas 3", {"payload": "Contoh teks 3"})

    print("=" * 60)
    print("Mulai eksekusi...")
    print("=" * 60)
    sup.run()

    report = sup.get_report()
    print(report)
    print("Hasil disimpan di: ", sup.config.result_path)

    # Contoh penggunaan sub-agen pendukung
    print("\n" + "=" * 60)
    print("CONTOH SUB AGEN PENDUNG")
    print("=" * 60)
    print(">>> Sub-Agent: Rangkuman")
    print(sub_agen_pelayan("ringkasan", "Hujan adalah proses alam..."))
    print("\n>>> Sub-Agent: Analisis")
    print(sub_agen_pelayan("analisis", "Hujan bermanfaat bagi pertanian..."))
    print("\n>>> Sub-Agent: Review")
    print(sub_agen_pelayan("review", "Teks ini sudah baik..."))


if __name__ == "__main__":
    main()

