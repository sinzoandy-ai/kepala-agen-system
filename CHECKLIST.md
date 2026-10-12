# Checklist Praktik Sistem Kepala Agen (Supervisor)

## Persiapan Lingkungan
- [ ] Pastikan Python 3.8+ terinstall (`python --version`)
- [ ] Buat folder proyek: `mkdir agent_project && cd agent_project`
- [ ] Simpan `main_supervisor.py` di folder proyek
- [ ] (Opsional) Simpan `test_kepala_agen.py` untuk uji coba

## Langkah 1: Import dan Konfigurasi
- [ ] Buka `main_supervisor.py`
- [ ] Pastikan class `Config` sudah terdefinisi
- [ ] Atur `agent_name`, `result_dir`, `max_workers` sesuai kebutuhan

## Langkah 2: Daftarkan Agent
- [ ] Buat fungsi agent (contoh: `def demo_agent(payload): ...`)
- [ ] Register agent ke supervisor:
  ```python
  sup.register_agent("nama_agent", demo_agent)
  ```

## Langkah 3: Tambahkan Tugas
- [ ] Gunakan `sup.add_task(name, payload, priority)` untuk setiap tugas
- [ ] Set `priority` (1 = tertinggi, mekanisme antar prioritas aktif)
- [ ] Payload bisa berupa dict, string, atau data apa saja

## Langkah 4: Jalankan Supervisor
- [ ] Panggil `sup.run()`
- [ ] Hasil disimpan otomatis ke file JSON di folder `agent_results/`
- [ ] Log ditulis ke `supervisor_log.json` dan `tasks_log.json`

## Langkah 5: Cek Hasil
- [ ] Buka `agent_results/supervisor_log.json`
- [ ] Verify: setiap tugas punya `task_id`, `total_score`, timestamp
- [ ] Buka `agent_results/tasks_log.json`
- [ ] Verify: setiap tugas punya `task_id`, `status`, `timestamp`

## Langkah 6: Gunakan Sub-Agen Pendukung
- [ ] Pilih sub-agen sesuai kebutuhan:
  - `summary` → Rangkuman (kunci: "ringkasan")
  - `analyze` → Analisis/ekstrak poin (kunci: "analisis", "poin")
  - `translate` → Terjemahan (kunci: "terjemah")
  - `review` → Review kualitas (kunci: "review")
- [ ] Panggil:
  ```python
  result = sub_agen_pelayan("ringkasan", "teks untuk diringkas...")
  ```

## Checklist Kualitas & Efisiensi
- [ ] Setiap tugas selesai dengan total_score >= 85.0
- [ ] Evaluator membagi skor: quality (80), efficiency (100), completeness (75)
- [ ] Log timestamps ada di setiap record
- [ ] File JSON valid (bisa dibuka dengan `json.load()`)

## Troubleshooting
- [ ] Jika TypeError "'dict' object is not callable" → periksa key "func" vs "fn" dalam SUBGAGEN_LIST
- [ ] Jika KeyError "fn" → gunakan `["func"]` atau `["fn"]` sesuai entry sub-agen
- [ ] Jika file tidak ada → pastikan `result_dir` dapat ditulis
- [ ] Jika skor rendah → periksa `max_expected_words` di Evaluator

## Lanjutan
- [ ] Tambah agent custom sesuai kebutuhan proyek
- [ ] Atur `use_parallel=True` untuk eksekusi paralel (max 3 tugas)
- [ ] Simpan contoh penggunaan sub-agen di `main()` untuk dokumentasi
