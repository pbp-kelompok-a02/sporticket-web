document.addEventListener('DOMContentLoaded', function() {

    // === HELPERS ===

    /**
     * Mengambil CSRF token dari form yang ada di base.html
     */
    function getCsrfToken() {
        const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return el ? el.value : '';
    }

    // Ambil event match_id dari form/modal atau dari container di halaman
    function getEventMatchId(formLike) {
        const fromForm = formLike && formLike.dataset && formLike.dataset.eventId;
        const fromContainer = document.getElementById('review-list-container')?.dataset?.eventId || document.getElementById('review-container')?.dataset?.eventId;
        return fromForm || fromContainer || null;
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
        const addModal = document.getElementById('addReviewModal');
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

    // === RATING SYSTEM FOR ADD MODAL ===
    let currentRating = 0;
    let currentEditRating = 0;

    function hoverStars(rating) {
        const stars = document.querySelectorAll('#rating-stars .rating-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.textContent = '★';
                star.style.color = '#FBBF24';
            } else {
                star.textContent = '☆';
                star.style.color = '#D1D5DB';
            }
        });
    }

    function resetStars() {
        const stars = document.querySelectorAll('#rating-stars .rating-star');
        stars.forEach((star, index) => {
            if (index < currentRating) {
                star.textContent = '★';
                star.style.color = '#FBBF24';
            } else {
                star.textContent = '☆';
                star.style.color = '#D1D5DB';
            }
        });
    }

    function setRating(rating) {
        currentRating = rating;
        document.getElementById('rating-value').value = rating;
        resetStars();
    }

    // === RATING SYSTEM FOR EDIT MODAL ===
    function hoverEditStars(rating) {
        const stars = document.querySelectorAll('#edit-rating-stars .edit-rating-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.textContent = '★';
                star.style.color = '#FBBF24';
            } else {
                star.textContent = '☆';
                star.style.color = '#D1D5DB';
            }
        });
    }

    function resetEditStars() {
        const stars = document.querySelectorAll('#edit-rating-stars .edit-rating-star');
        stars.forEach((star, index) => {
            if (index < currentEditRating) {
                star.textContent = '★';
                star.style.color = '#FBBF24';
            } else {
                star.textContent = '☆';
                star.style.color = '#D1D5DB';
            }
        });
    }

    function setEditRating(rating) {
        currentEditRating = rating;
        document.getElementById('edit-rating-value').value = rating;
        resetEditStars();
    }

    // === TAMBAH REVIEW ===

    window.openAddModal = function(eventId) {
        const modal = document.getElementById('addReviewModal');
        if (modal) {
            // Reset form dan rating
            document.getElementById('add-review-form').reset();
            currentRating = 0;
            resetStars();
            document.getElementById('rating-value').value = '';
            
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }
    
    window.closeAddModal = function() {
        const modal = document.getElementById('addReviewModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    }

    const addReviewForm = document.getElementById('add-review-form');
    if (addReviewForm) {
        addReviewForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const eventId = getEventMatchId();
            if (!eventId) {
                showToast('Error: Event ID not found', 'error');
                return;
            }
            
            // Validasi rating
            if (!currentRating) {
                showToast('Please select a rating', 'error');
                return;
            }
            
            const formData = new FormData(this);
            
            fetch(`/review/${eventId}/create/`, {
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
                    closeAddModal();
                    showToast(res.message || 'Review berhasil ditambahkan', 'success');
                    
                    // Refresh halaman untuk menampilkan review baru
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
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

    window.openEditModal = function(reviewId, rating, komentar) {
        const modal = document.getElementById('reviewEditModal');
        if (modal) {
            // Set nilai form
            document.getElementById('edit-review-id').value = reviewId;
            document.getElementById('edit-komentar').value = komentar || '';
            
            // Set rating stars
            currentEditRating = rating;
            setEditRating(rating);
            
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    window.closeEditModal = function() {
        const modal = document.getElementById('reviewEditModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    }

    const editReviewForm = document.getElementById('edit-review-form');
    if (editReviewForm) {
        editReviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const reviewId = document.getElementById('edit-review-id').value;
            if (!reviewId) {
                showToast('Review id tidak ditemukan', 'error');
                return;
            }
            
            const eventId = getEventMatchId();
            if (!eventId) {
                showToast('Error: Event ID not found (edit)', 'error');
                return;
            }
            
            // Validasi rating
            if (!currentEditRating) {
                showToast('Please select a rating', 'error');
                return;
            }
            
            const formData = new FormData(this);

            fetch(`/review/${eventId}/${reviewId}/edit/`, {
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
                    closeEditModal();
                    showToast(res.message || 'Review berhasil diupdate', 'success');
                    
                    // Refresh halaman untuk menampilkan perubahan
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
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

    window.deleteReview = function(eventId, reviewId) {
        if (!confirm('Are you sure to delete this review?')) return;
        
        if (!eventId) {
            eventId = getEventMatchId();
        }
        
        if (!eventId) {
            showToast('Error: Event ID not found (delete)', 'error');
            return;
        }

        const params = new URLSearchParams();
        params.append('csrfmiddlewaretoken', getCsrfToken());

        fetch(`/review/${eventId}/${reviewId}/delete/`, {
            method: 'POST',
            body: params, 
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => safeJSON(response))
        .then(res => {
            if (res && res.success) {
                const card = document.getElementById(`review-${reviewId}`);
                if (card) {
                    // Efek fade out
                    card.style.transition = 'opacity 0.3s ease';
                    card.style.opacity = '0';
                    setTimeout(() => {
                        card.remove();
                        // Jika tidak ada review lagi, refresh halaman
                        const remainingReviews = document.querySelectorAll('[id^="review-"]');
                        if (remainingReviews.length === 0) {
                            setTimeout(() => {
                                window.location.reload();
                            }, 500);
                        }
                    }, 300);
                }
                showToast(res.message || 'Review berhasil dihapus', 'success');
            } else {
                showToast(res && res.message ? res.message : 'Gagal menghapus review', 'error');
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
        const eventId = getEventMatchId();
        if (!eventId) return;

        // Atur style tombol aktif/non-aktif
        if (filterAllBtn && filterMyBtn) {
            if (filter === 'my') {
                filterMyBtn.classList.remove('bg-gray-200', 'text-[#537FB9]');
                filterMyBtn.classList.add('bg-[#537FB9]', 'text-white');
                filterAllBtn.classList.remove('bg-[#537FB9]', 'text-white');
                filterAllBtn.classList.add('bg-gray-200', 'text-[#537FB9]');
            } else {
                filterAllBtn.classList.remove('bg-gray-200', 'text-[#537FB9]');
                filterAllBtn.classList.add('bg-[#537FB9]', 'text-white');
                filterMyBtn.classList.remove('bg-[#537FB9]', 'text-white');
                filterMyBtn.classList.add('bg-gray-200', 'text-[#537FB9]');
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
            } else {
                showToast('Gagal memuat ulang review', 'error');
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