**Nama anggota kelompok**:
Laudya Michelle Alexandra (2406419594)
Ali Akbar Murthadha (2406495754)
Fidan Khalil Salman (2406408501)
Ahmad Aqeel Saniy (2306275941)
Haris Azzahra Lunaaya (2406425930)

Tema            : Penjualan tiket olahraga (5 jenis olahraga)
Nama Aplikasi   : SPORTICKET

**Deskripsi Aplikasi**
Sporticket adalah platform penjualan tiket digital pertandingan olahraga yang dirancang untuk memberikan kemudahan kepada penggemar olahraga sepak bola, basket, voli, badminton, dan tenis dalam membeli tiket untuk event-event olahraga favorit mereka. Aplikasi ini menawarkan pengalaman pengguna yang cepat, aman, dan efisien dalam membeli tiket untuk berbagai event olahraga, dengan integrasi pemilihan kategori tiket (reguler atau VIP), sistem notifikasi, dan akses mudah ke riwayat pembelian. Fitur-fitur lengkap aplikasi Sporticket dijelaskan lebih lanjut dalam bagian daftar modul.

**Daftar Modul**
1. Modul Event Pertandingan (Admin)
    Model: Event (nama pertandingan, home team, away team, deskripsi, poster, venue, date, kapasitas).
    CRUD:
        Create → admin tambah event baru
        Read → lihat daftar event (detail event ada di card event)
        Update → edit detail event (misalnya ganti venue, ubah jadwal, update deskripsi).
        Delete → hapus event lama.
    AJAX: menampilkan notifikasi sukses/gagal ketika admin tambah/edit/hapus event tanpa reload.

2. Modul Tiket (Admin)
    Model: Ticket (event [FK ke event], kategori tiket: VIP/Reguler, harga, stok).
    CRUD:
        Create → admin tambah tiket (reguler/vip) untuk event.
        Read → tampilkan daftar tiket per event.
        Update → admin update stok/harga tiket.
        Delete → hapus kategori tiket tertentu.
    AJAX: update stok tiket dan hapus tiket secara realtime tanpa reload halaman.

3. Modul Pesanan (Buyer)
    Model: Order (user, tiket, jumlah, status: pending/confirmed/cancelled).
    CRUD:
        Create → user buat pesanan tiket.
        Read → user lihat riwayat pesanan/pembelian.
        Update → user bisa ubah jumlah tiket ketika masih pending.
        Delete → user bisa hapus/batalkan pesanan ketika pesanan pending atau sudah confirmed.
    AJAX: submit order, hapus order, edit order via AJAX → muncul notifikasi sukses/gagal tanpa reload.

4. Modul Review Event (Buyer)
    Model: Review (user, event [FK], rating, komentar, tanggal).
    CRUD:
        Create → user kasih review pada event yang dihadiri.
        Read → tampilkan daftar review di halaman detail event.
        Update → user bisa edit review-nya.
        Delete → user hapus review sendiri.
    AJAX: tambah review tanpa reload → langsung muncul di daftar review.

5. Modul Akun (Buyer & Admin)
    Model: User (nama, email, password, role [Admin/Buyer], nomor_telepon, photo_profile).
    CRUD:
        Create → Registrasi (User membuat akun baru, hanya untuk akun Buyer karena Admin adalah superuser).
        Read → Lihat detail profil pengguna (nama, email, no. telepon, role)
        Update → Edit informasi profil (misalnya ganti nama, nomor telepon) dan ubah password.
        Delete → Hapus Akun 
    AJAX: update detail profil tanpa reload halaman

**Sumber initial dataset**
Sumber Initial Dataset adalah synthetic data.
Synthetic data yang maksudnya: Datanya tidak diambil langsung dari website resmi atau API, tapi dibuat secara manual dan acak dengan data yang mirip dunia nyata. Ini dilakukan untuk mencegah adanya copyright dan mudahnya mengelola data yang sudah bersih dan seperti nyata.
Dataset akan disimpan di csv file. 
Dataset-dataset ini untuk:
    Data pertandingan olahraga
    Data kursi tiket setiap pertandingannya 

Sepak bola 
https://www.premierleague.com/en/matches?competition=8&season=2025&matchweek=7&month=10
Reference for ticketing  : https://tickets.manutd.com/en-GB/events/manchester%20united%20v%20west%20ham%20united/2025-12-3_20.00/old%20trafford?hallmap

Basket:
https://www.nba.com/games
Reference for ticketing: https://www.ticketmaster.com/golden-state-warriors-vs-phoenix-suns-san-francisco-california-12-20-2025/event/1C00630BB090660C?artistid=805946&brand=warriors&f_simplified_filter=true&f_enable_merch_slot=true

Voli:
https://en.volleyballworld.com/global-schedule#fromDate=2025-10-03&yearseason=2025
Reference for ticketing:
https://am.ticketmaster.com/columbusfury/buy/ism/MjZDRkZT

Badminton:
https://www.flashscore.com/badminton/
Reference for ticketing : https://www.ticketmaster.dk/event/victor-denmark-open-2025-finaler-billetter/2028697464

Tennis:
https://www.espn.com/tennis/scoreboard
Reference for ticketing:
https://seatgeek.com/the-garden-cup-tickets/tennis/2025-12-08-7-pm/17721058?quantity=1

**Deskripsi peran pengguna**
- Admin (Superuser)
    Admin dapat membuat event pertandingan dan tiket pertandingan, melihat tiket dan event yang ada, mengedit tiket pertandingan dan event yang ada (ganti jadwal / lokasi), dan menghapus tiket pertandingan dan event yang ada.
- Pembeli (Regular user)
    Pembeli dapat melihat detail tiket dan riwayat pembelian, membeli tiket pertandingan, ganti/update jumlah tiket yang dibeli, membatalkan pembelian tiket, membuat review event, mengedit review event yang ia buat, dan menghapus review event yang ia buat.


**Tautan PWS** = https://laudya-michelle-sporticket.pbp.cs.ui.ac.id/