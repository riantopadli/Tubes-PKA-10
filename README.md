# Tubes PKA: SIMANDIS (Sistem Manajemen Distribusi BBM)

Aplikasi ini adalah simulasi optimasi jalur distribusi BBM (Pertamina Patra Niaga) di wilayah Balikpapan. Aplikasi ini membandingkan algoritma **Dijkstra** dan **A* (A-Star)** untuk mencari rute terpendek dengan fitur *Multi-Stop Routing*.

## 📋 Fitur Utama
- **Peta Interaktif:** Visualisasi rute menggunakan peta digital (Folium).
- **Perbandingan Algoritma:** Dijkstra vs A*.
- **10 Skenario Dunia Nyata:** Termasuk simulasi stok kritis, jalur industri, dan *panic buying*.
- **Manajemen Ritase:** Kalkulasi waktu tempuh dan urutan kunjungan SPBU otomatis.

## 🛠️ Prasyarat (Requirements)
Pastikan kamu sudah menginstal **Python** (versi 3.8 ke atas) di komputer kamu.

### Library yang Perlu Diinstall
Buka terminal (Command Prompt/PowerShell) di VS Code, lalu jalankan perintah berikut untuk menginstal semua *library* yang dibutuhkan:

```bash
pip install streamlit folium streamlit-folium pandas