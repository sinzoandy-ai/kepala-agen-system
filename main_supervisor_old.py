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
    evaluator_threshold: float = 70.0
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
        """Skor kelengkapan: cek ada isi / selesai."""
        if output is None:
            return 0.0
        text = output if isinstance(output, str) else str(output)
        text = text.strip()
        if not text:
            return 0.0
        return 70.0 + (5.0 if len(text) > 20 else 0)


# ============================================================
# 5. RESULT STORE (PENYIMPAN HASIL)
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
            self._process_task(task)

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
    result = f"Ringkasan dari: {text[:80]}..."
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

