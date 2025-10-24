document.addEventListener('DOMContentLoaded', function() {

    // === HELPERS ===

    /**
     * Mengambil CSRF token dari form yang ada di base.html
     */
    function getCsrfToken() {
        const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return el ? el.value : '';
    }

    // parse JSON dengan aman (fallback ke teks jika bukan JSON)
    async function safeJSON(response) {
        const text = await response.text();
        try {
            return JSON.parse(text);
        } catch (e) {
            return { success: false, raw: text, status: response.status, ok: response.ok };
        }
    }

    // close modals saat klik backdrop
    document.addEventListener('click', function(e) {
        const addModal = document.getElementById('reviewAddModal');
        const editModal = document.getElementById('reviewEditModal');
        if (addModal && e.target === addModal) closeAddModal();
        if (editModal && e.target === editModal) closeEditModal();
    });

    // close modal saat tekan Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAddModal();
            closeEditModal();
        }
    });
    /**
     * Menampilkan notifikasi toast
     */
    window.showToast = function(msg, type = 'success') {
        const color = type === 'error' ? 'bg-red-500' : 'bg-[#537FB9]';
        const toast = document.createElement('div');
        toast.className = `${color} text-white px-4 py-2 rounded-xl fixed bottom-5 right-5 shadow-md font-[Kanit] opacity-0 transition-opacity`;
        toast.style.zIndex = '100';
        toast.textContent = msg;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.style.opacity = '1', 100);
        setTimeout(() => toast.style.opacity = '0', 2500);
        setTimeout(() => toast.remove(), 3000);
    }

    // === TAMBAH REVIEW ===

    window.openAddModal = function(eventId) {
        const form = document.getElementById('addReviewForm');
        const modal = document.getElementById('reviewAddModal');
        if (form && modal) {
            form.dataset.eventId = eventId;
            // modal sudah memiliki class 'flex' di template; cukup toggle hidden
            modal.classList.remove('hidden');
        }
    }
    
    window.closeAddModal = function() {
        const modal = document.getElementById('reviewAddModal');
        const form = document.getElementById('addReviewForm');
        if (modal) {
            modal.classList.add('hidden');
        }
        if (form) form.reset();
    }

    const addReviewForm = document.getElementById('addReviewForm');
    if (addReviewForm) {
        addReviewForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const eventId = this.dataset.eventId || this.getAttribute('data-event-id');
            if (!eventId) {
                showToast('Error: Event ID not found', 'error');
                return;
            }
            
            const formData = new FormData(this); // Menggunakan FormData
            
            fetch(`/review/${eventId}/create/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest' // Penting untuk Django
                }
            })
            .then(response => safeJSON(response))
            .then(res => {
                if (res && res.success) {
                    // Jika ada container review, insert; else trigger reload via filter
                    const list = document.getElementById('review-container') || document.getElementById('review-list-container');
                    if (list && (res.html || res.review_html)) {
                        list.insertAdjacentHTML('afterbegin', res.html || res.review_html);
                    } else {
                        // fallback: trigger filter-all jika ada, atau reload halaman
                        document.getElementById('filter-all')?.click();
                        setTimeout(() => {
                            if (!document.getElementById('filter-all')) location.reload();
                        }, 700);
                    }
                    closeAddModal();
                    showToast(res.message || 'Review berhasil ditambahkan', 'success');
                    this.reset(); // Mereset form
                } else {
                    showToast(res && res.message ? res.message : 'Gagal menambah review', 'error');
                }
            })
            .catch((err) => {
                console.error(err);
                showToast('Terjadi kesalahan server', 'error');
            });
        });
    }

    // === EDIT REVIEW ===

    window.openEditModal = function(button) {
        // support passing element or object
        let el = button;
        if (!button) return;
        if (typeof button === 'string' || typeof button === 'number') {
            el = document.querySelector(`[data-review-id="${button}"]`) || document.querySelector(`#review-${button}`);
        }
        const id = el?.dataset?.reviewId || el?.getAttribute('data-review-id');
        const rating = el?.dataset?.reviewRating;
        const komentar = el?.dataset?.reviewKomentar;

        const inputId = document.getElementById('edit-review-id');
        const inputRating = document.getElementById('edit-rating');
        const inputKomentar = document.getElementById('edit-komentar');

        if (inputId) inputId.value = id || '';
        if (inputRating) inputRating.value = rating || '5';
        if (inputKomentar) inputKomentar.value = komentar || '';

        const modal = document.getElementById('reviewEditModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    window.closeEditModal = function() {
        const modal = document.getElementById('reviewEditModal');
        const form = document.getElementById('editReviewForm');
        if (modal) modal.classList.add('hidden');
        if (form) form.reset();
    }

    const editReviewForm = document.getElementById('editReviewForm');
    if (editReviewForm) {
        editReviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const reviewId = document.getElementById('edit-review-id')?.value;
            if (!reviewId) {
                showToast('Review id tidak ditemukan', 'error');
                return;
            }
            const formData = new FormData(this);

            fetch(`/review/${reviewId}/edit/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => safeJSON(response))
            .then(res => {
                if (res && res.success) {
                    const oldCard = document.getElementById(`review-${reviewId}`);
                    if (oldCard && (res.html || res.review_html)) {
                        // replace card dengan html dari server
                        const tmp = document.createElement('div');
                        tmp.innerHTML = res.html || res.review_html;
                        const newNode = tmp.firstElementChild;
                        if (newNode && oldCard.parentNode) oldCard.parentNode.replaceChild(newNode, oldCard);
                    } else if (oldCard && res.review) {
                        // update minimal: komentar
                        const p = oldCard.querySelector('p.text-gray-700') || oldCard.querySelector('p');
                        if (p && res.review.komentar !== undefined) p.textContent = res.review.komentar;
                    } else {
                        // fallback
                        setTimeout(() => location.reload(), 600);
                    }
                    closeEditModal();
                    showToast(res.message || 'Review berhasil diupdate', 'success');
                } else {
                    showToast(res && res.message ? res.message : 'Gagal memperbarui review', 'error');
                }
            })
            .catch((err) => {
                console.error(err);
                showToast('Terjadi kesalahan server', 'error');
            });
        });
    }

    // === DELETE REVIEW ===

    window.deleteReview = function(id) {
        if (!confirm('Are you sure to delete this review?')) return;
        
        // Untuk POST data non-form, kita kirim sebagai URLSearchParams
        const params = new URLSearchParams();
        params.append('csrfmiddlewaretoken', getCsrfToken());

        fetch(`/review/${id}/delete/`, {
            method: 'POST',
            body: params, 
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => safeJSON(response))
        .then(res => {
            if (res && res.success) {
                const card = document.getElementById(`review-${id}`);
                if (card) {
                    // Efek fade out versi Vanilla JS
                    card.style.transition = 'opacity 0.3s ease';
                    card.style.opacity = '0';
                    setTimeout(() => {
                        card.remove();
                    }, 300);
                }
                showToast(res.message || 'Review is deleted', 'success');
            } else {
                showToast(res && res.message ? res.message : 'Failed to delete review', 'error');
            }
        })
        .catch((err) => {
            console.error(err);
            showToast('Terjadi kesalahan server', 'error');
        });
    }

    // === FILTER REVIEW ===

    const filterAllBtn = document.getElementById('filter-all');
    const filterMyBtn = document.getElementById('filter-my');
    const reviewListContainer = document.getElementById('review-list-container');

    function handleFilterClick(e) {
        const filter = e.currentTarget?.dataset?.filter || 'all';
        const eventId = reviewListContainer?.dataset?.eventId || document.getElementById('review-container')?.dataset?.eventId;
        if (!eventId) return;

        // Atur style tombol aktif/non-aktif jika kedua tombol ada
        if (filterAllBtn && filterMyBtn) {
            if (filter === 'my') {
                filterMyBtn.classList.replace('bg-gray-200', 'bg-[#537FB9]');
                filterMyBtn.classList.replace('text-[#537FB9]', 'text-white');
                filterAllBtn.classList.replace('bg-[#537FB9]', 'bg-gray-200');
                filterAllBtn.classList.replace('text-white', 'text-[#537FB9]');
            } else {
                filterAllBtn.classList.replace('bg-gray-200', 'bg-[#537FB9]');
                filterAllBtn.classList.replace('text-[#537FB9]', 'text-white');
                filterMyBtn.classList.replace('bg-[#537FB9]', 'bg-gray-200');
                filterMyBtn.classList.replace('text-white', 'text-[#537FB9]');
            }
        }

        fetch(`/review/${eventId}/filter/?type=${encodeURIComponent(filter)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => safeJSON(response))
            .then(res => {
                if (res && res.html && reviewListContainer) {
                    reviewListContainer.innerHTML = res.html;
                } else if (res && res.success && res.html && reviewListContainer) {
                    reviewListContainer.innerHTML = res.html;
                } else {
                    location.reload();
                }
            })
            .catch((err) => {
                console.error(err);
                showToast('Gagal memuat review', 'error');
            });
    }

    if (filterAllBtn) filterAllBtn.addEventListener('click', handleFilterClick);
    if (filterMyBtn) filterMyBtn.addEventListener('click', handleFilterClick);

});