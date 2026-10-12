#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uji Coba (Test) untuk Sistem Kepala Agen (Supervisor)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_supervisor import Supervisor, sub_agen_pelayan, SUBGAGEN_LIST

def test_supervisor():
    print("=" * 60)
    print("TEST 1: Supervisor Dasar")
    print("=" * 60)
    sup = Supervisor()
    sup.register_agent("demo", lambda p: f"Hasil: {str(p)[:50]}...")
    
    sup.add_task("Tugas Uji 1", {"data": "satu"})
    sup.add_task("Tugas Uji 2", {"data": "dua"})
    sup.add_task("Tugas Uji 3", {"data": "tiga"})
    
    results = sup.run()
    
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    assert all(r["total_score"] == 85.0 for r in results), "All tasks should score 85.0"
    
    print(f"[PASS] Total hasil: {len(results)}")
    print(f"[PASS] Skor rata-rata: {sum(r['total_score'] for r in results) / 3:.1f}")
    return True

def test_sub_agen():
    print("\n" + "=" * 60)
    print("TEST 2: Sub-Agen Pendukung")
    print("=" * 60)
    
    # Test summary sub-agent
    summary = sub_agen_pelayan("ringkasan", "Hujan adalah proses alam yang penting.")
    assert "Ringkasan cepat" in summary, f"Summary sub-agent failed: {summary}"
    print(f"[PASS] Summary: {summary}")
    
    # Test analyze sub-agent
    analyze = sub_agen_pelayan("analisis", "Hujan bermanfaat bagi pertanian.")
    assert "Analisis:" in analyze, f"Analyze sub-agent failed: {analyze}"
    print(f"[PASS] Analyze: {analyze}")
    
    # Test translate sub-agent
    translate = sub_agen_pelayan("terjemah", "Hujan dalam Bahasa Inggris: Rain")
    assert "Terjemahan:" in translate, f"Translate sub-agent failed: {translate}"
    print(f"[PASS] Translate: {translate}")
    
    # Test review sub-agent
    review = sub_agen_pelayan("review", "Teks ini sudah baik.")
    assert "Review:" in review, f"Review sub-agent failed: {review}"
    print(f"[PASS] Review: {review}")
    
    # Test unknown task (defaults to summary)
    default = sub_agen_pelayan("tugas tidak dikenal", "data")
    assert "Ringkasan cepat" in default, f"Default sub-agent failed: {default}"
    print(f"[PASS] Default: {default}")
    
    return True

def test_sub_agen_list():
    print("\n" + "=" * 60)
    print("TEST 3: Daftar Sub-Agen")
    print("=" * 60)
    
    assert "summary" in SUBGAGEN_LIST, "Missing 'summary' sub-agent"
    assert "analyze" in SUBGAGEN_LIST, "Missing 'analyze' sub-agent"
    assert "translate" in SUBGAGEN_LIST, "Missing 'translate' sub-agent"
    assert "review" in SUBGAGEN_LIST, "Missing 'review' sub-agent"
    
    assert "name" in SUBGAGEN_LIST["summary"], "Missing 'name' in summary"
    assert "description" in SUBGAGEN_LIST["summary"], "Missing 'description' in summary"
    
    print(f"[PASS] Total sub-agen: {len(SUBGAGEN_LIST)}")
    for key, agent in SUBGAGEN_LIST.items():
        print(f"  - {key}: {agent['name']}")
    
    return True

def test_task_manager():
    print("\n" + "=" * 60)
    print("TEST 4: Task Manager")
    print("=" * 60)
    
    from main_supervisor import TaskManager
    tm = TaskManager()
    
    tm.add_task("Tugas A", {"payload": "data A"})
    tm.add_task("Tugas B", {"payload": "data B"}, priority=2)
    tm.add_task("Tugas C", {"payload": "data C"}, priority=1)
    
    pending = tm.get_pending()
    assert len(pending) == 3, f"Expected 3 pending tasks, got {len(pending)}"
    
    # Get next (should be highest priority = 2)
    next_task = tm.get_next()
    assert next_task.priority == 2, f"Expected priority 2, got {next_task.priority}"
    
    tm.mark_done("dummy")  # Should not fail
    print(f"[PASS] TaskManager: {len(pending)} pending, next priority={next_task.priority}")
    
    return True

if __name__ == "__main__":
    all_passed = True
    
    try:
        test_supervisor()
    except Exception as e:
        print(f"[FAIL] Test 1: {e}")
        all_passed = False
    
    try:
        test_sub_agen()
    except Exception as e:
        print(f"[FAIL] Test 2: {e}")
        all_passed = False
    
    try:
        test_sub_agen_list()
    except Exception as e:
        print(f"[FAIL] Test 3: {e}")
        all_passed = False
    
    try:
        test_task_manager()
    except Exception as e:
        print(f"[FAIL] Test 4: {e}")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("SEMUA TEST MENERIMA (ALL TESTS PASSED)")
    else:
        print("ADA BEBERAPA TEST GAGAL")
    print("=" * 60)
