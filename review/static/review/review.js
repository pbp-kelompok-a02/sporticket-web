document.addEventListener('DOMContentLoaded', function() {
    console.log('Review JS loaded');

    // === GLOBAL VARIABLES ===
    let currentRating = 0;
    let currentEditRating = 0;

    // === HELPERS ===
    function getCsrfToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    function getEventMatchId() {
        const reviewListContainer = document.getElementById('review-list-container');
        const reviewContainer = document.getElementById('review-container');
        
        if (reviewListContainer && reviewListContainer.dataset.eventId) {
            return reviewListContainer.dataset.eventId;
        }
        if (reviewContainer && reviewContainer.dataset.eventId) {
            return reviewContainer.dataset.eventId;
        }
        
        const urlMatch = window.location.pathname.match(/\/review\/([^\/]+)/);
        if (urlMatch) return urlMatch[1];
        
        console.error('Event ID not found in any container');
        return null;
    }

    async function safeJSON(response) {
        const text = await response.text();
        try {
            return JSON.parse(text);
        } catch (e) {
            console.error('JSON parse error:', e);
            return { success: false, error: 'Invalid JSON response', raw: text };
        }
    }

    // === TOAST FUNCTION ===
    window.showToast = function(msg, type = 'success') {
        console.log('Toast:', msg, type);
        document.querySelectorAll('.toast-message').forEach(toast => toast.remove());
        
        const color = type === 'error' ? 'bg-red-500' : 'bg-[#537FB9]';
        const toast = document.createElement('div');
        toast.className = `toast-message ${color} text-white px-6 py-3 rounded-lg fixed bottom-5 right-5 shadow-lg font-[Kanit] z-[10000] transition-all duration-300 transform translate-y-10 opacity-0`;
        toast.textContent = msg;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.remove('translate-y-10', 'opacity-0');
            toast.classList.add('translate-y-0', 'opacity-100');
        }, 100);
        
        setTimeout(() => {
            toast.classList.remove('translate-y-0', 'opacity-100');
            toast.classList.add('translate-y-10', 'opacity-0');
        }, 3000);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3300);
    }

    // === RATING SYSTEM FUNCTIONS ===
    function hoverStars(rating) {
        const stars = document.querySelectorAll('#rating-stars .rating-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.textContent = '★';
                star.style.color = '#FBBF24';
            } else {
                star.textContent = '☆';
                star.style.color = '#9CA3AF';
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
                star.style.color = '#9CA3AF';
            }
        });
    }

    function setRating(rating) {
        console.log('Setting rating:', rating);
        currentRating = rating;
        const ratingInput = document.getElementById('rating-value');
        if (ratingInput) {
            ratingInput.value = rating;
            console.log('Rating input value set to:', ratingInput.value);
        }
        resetStars();
    }

    function hoverEditStars(rating) {
        const stars = document.querySelectorAll('#edit-rating-stars .edit-rating-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.textContent = '★';
                star.style.color = '#FBBF24';
            } else {
                star.textContent = '☆';
                star.style.color = '#9CA3AF';
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
                star.style.color = '#9CA3AF';
            }
        });
    }

    function setEditRating(rating) {
        currentEditRating = rating;
        const ratingInput = document.getElementById('edit-rating-value');
        if (ratingInput) ratingInput.value = rating;
        resetEditStars();
    }

    // === RATING EVENT DELEGATION ===
    function initializeRatingStars() {
        // Add modal stars - Event delegation
        const ratingContainer = document.getElementById('rating-stars');
        if (ratingContainer) {
            ratingContainer.addEventListener('click', function(e) {
                if (e.target.classList.contains('rating-star')) {
                    const stars = Array.from(this.querySelectorAll('.rating-star'));
                    const index = stars.indexOf(e.target);
                    if (index !== -1) {
                        setRating(index + 1);
                    }
                }
            });

            ratingContainer.addEventListener('mouseover', function(e) {
                if (e.target.classList.contains('rating-star')) {
                    const stars = Array.from(this.querySelectorAll('.rating-star'));
                    const index = stars.indexOf(e.target);
                    if (index !== -1) {
                        hoverStars(index + 1);
                    }
                }
            });

            ratingContainer.addEventListener('mouseout', resetStars);
        }

        // Edit modal stars - Event delegation
        const editRatingContainer = document.getElementById('edit-rating-stars');
        if (editRatingContainer) {
            editRatingContainer.addEventListener('click', function(e) {
                if (e.target.classList.contains('edit-rating-star')) {
                    const stars = Array.from(this.querySelectorAll('.edit-rating-star'));
                    const index = stars.indexOf(e.target);
                    if (index !== -1) {
                        setEditRating(index + 1);
                    }
                }
            });

            editRatingContainer.addEventListener('mouseover', function(e) {
                if (e.target.classList.contains('edit-rating-star')) {
                    const stars = Array.from(this.querySelectorAll('.edit-rating-star'));
                    const index = stars.indexOf(e.target);
                    if (index !== -1) {
                        hoverEditStars(index + 1);
                    }
                }
            });

            editRatingContainer.addEventListener('mouseout', resetEditStars);
        }
    }

    // === MODAL FUNCTIONS ===
    const addReviewBtn = document.getElementById('add-review-btn');
    if (addReviewBtn) {
        addReviewBtn.addEventListener('click', function() {
            const eventId = this.getAttribute('data-event-id');
            openAddModal(eventId);
        });
    }

    window.openAddModal = function(eventIdFromButton = null) {
        console.log('openAddModal called, eventIdFromButton:', eventIdFromButton);
        
        const modal = document.getElementById('addReviewModal');
        if (!modal) {
            console.error('addReviewModal element not found!');
            showToast('Modal element not found', 'error');
            return;
        }

        // Check if user already has a review
        if (window.userHasReview) {
            showToast('You have already submitted a review for this event. You can edit or delete your existing review.', 'error');
            return;
        }

        // Reset state
        currentRating = 0;
        resetStars();
        
        const ratingInput = document.getElementById('rating-value');
        if (ratingInput) ratingInput.value = '';
        
        const form = document.getElementById('add-review-form');
        if (form) form.reset();

        // Show modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        console.log('Add modal opened successfully');
    };

    window.closeAddModal = function() {
        const modal = document.getElementById('addReviewModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    };

    window.openEditModal = function(reviewId, rating, komentar) {
        console.log('openEditModal called:', { reviewId, rating, komentar });
        
        const modal = document.getElementById('reviewEditModal');
        if (!modal) {
            console.error('reviewEditModal element not found!');
            return;
        }

        // Set values
        document.getElementById('edit-review-id').value = reviewId;
        document.getElementById('edit-komentar').value = komentar || '';
        
        // Set rating
        currentEditRating = rating;
        setEditRating(rating);

        // Show modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    };

    window.closeEditModal = function() {
        const modal = document.getElementById('reviewEditModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    };

    // === EVENT LISTENERS ===
    function initializeEventListeners() {
        // Close modals on backdrop click
        document.addEventListener('click', function(e) {
            const addModal = document.getElementById('addReviewModal');
            const editModal = document.getElementById('reviewEditModal');
            
            if (addModal && e.target === addModal) closeAddModal();
            if (editModal && e.target === editModal) closeEditModal();
        });

        // Close modals on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeAddModal();
                closeEditModal();
            }
        });

        // Add review form submission
        const addReviewForm = document.getElementById('add-review-form');
        if (addReviewForm) {
            addReviewForm.addEventListener('submit', handleAddReviewSubmit);
        }

        // Edit review form submission
        const editReviewForm = document.getElementById('edit-review-form');
        if (editReviewForm) {
            editReviewForm.addEventListener('submit', handleEditReviewSubmit);
        }

        // Initialize rating stars with event delegation
        initializeRatingStars();
    }

    // === FORM HANDLERS ===
    async function handleAddReviewSubmit(e) {
        e.preventDefault();
        console.log('Add review form submitted');
        
        const eventId = getEventMatchId();
        console.log('Found eventId:', eventId);
        
        if (!eventId) {
            showToast('Error: Event ID not found. Please refresh the page.', 'error');
            return;
        }

        // Validate rating
        if (!currentRating) {
            showToast('Please select a rating', 'error');
            return;
        }

        const formData = new FormData(e.target);
        
        try {
            console.log('Sending request to:', `/review/${eventId}/create/`);
            
            const response = await fetch(`/review/${eventId}/create/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await safeJSON(response);
            console.log('Add review response:', result);

            if (result.success) {
                showToast(result.message || 'Review berhasil ditambahkan', 'success');
                closeAddModal();
                
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showToast(result.message || 'Gagal menambah review', 'error');
            }
        } catch (error) {
            console.error('Add review error:', error);
            showToast('Terjadi kesalahan server', 'error');
        }
    }

    async function handleEditReviewSubmit(e) {
        e.preventDefault();
        console.log('Edit review form submitted');
        
        const reviewId = document.getElementById('edit-review-id').value;
        const eventId = getEventMatchId();
        
        if (!reviewId) {
            showToast('Review ID not found', 'error');
            return;
        }
        
        if (!eventId) {
            showToast('Event ID not found', 'error');
            return;
        }

        // Validate rating
        if (!currentEditRating) {
            showToast('Please select a rating', 'error');
            return;
        }

        const formData = new FormData(e.target);

        try {
            const response = await fetch(`/review/${eventId}/${reviewId}/edit/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await safeJSON(response);
            console.log('Edit review response:', result);

            if (result.success) {
                showToast(result.message || 'Review berhasil diperbarui', 'success');
                closeEditModal();
                
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showToast(result.message || 'Gagal memperbarui review', 'error');
            }
        } catch (error) {
            console.error('Edit review error:', error);
            showToast('Terjadi kesalahan server', 'error');
        }
    }

    // === DELETE REVIEW ===
    window.deleteReview = async function(eventId, reviewId) {
        if (!confirm('Are you sure you want to delete this review?')) {
            return;
        }

        if (!eventId) {
            eventId = getEventMatchId();
        }

        if (!eventId) {
            showToast('Event ID not found', 'error');
            return;
        }

        if (!reviewId) {
            showToast('Review ID not found', 'error');
            return;
        }

        const params = new URLSearchParams();
        params.append('csrfmiddlewaretoken', getCsrfToken());

        try {
            const response = await fetch(`/review/${eventId}/${reviewId}/delete/`, {
                method: 'POST',
                body: params,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await safeJSON(response);
            console.log('Delete review response:', result);

            if (result.success) {
                showToast(result.message || 'Review berhasil dihapus', 'success');
                
                const card = document.getElementById(`review-${reviewId}`);
                if (card) {
                    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(-10px)';
                    
                    setTimeout(() => {
                        card.remove();
                        
                        const remainingReviews = document.querySelectorAll('[id^="review-"]');
                        if (remainingReviews.length === 0) {
                            setTimeout(() => window.location.reload(), 500);
                        }
                    }, 300);
                } else {
                    setTimeout(() => window.location.reload(), 500);
                }
            } else {
                showToast(result.message || 'Gagal menghapus review', 'error');
            }
        } catch (error) {
            console.error('Delete review error:', error);
            showToast('Terjadi kesalahan server', 'error');
        }
    };

    // === FILTER REVIEWS ===
    const filterAllBtn = document.getElementById('filter-all');
    const filterMyBtn = document.getElementById('filter-my');

    function handleFilterClick(e) {
        const filter = e.currentTarget?.dataset?.filter || 'all';
        const eventId = getEventMatchId();
        
        if (!eventId) {
            showToast('Event ID not found for filtering', 'error');
            return;
        }

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
        .then(result => {
            const reviewListContainer = document.getElementById('review-list-container');
            if (result.html && reviewListContainer) {
                reviewListContainer.innerHTML = result.html;
            } else {
                showToast('Gagal memuat ulang review', 'error');
            }
        })
        .catch(error => {
            console.error('Filter error:', error);
            showToast('Gagal memuat review', 'error');
        });
    }

    if (filterAllBtn) filterAllBtn.addEventListener('click', handleFilterClick);
    if (filterMyBtn) filterMyBtn.addEventListener('click', handleFilterClick);

    // === INITIALIZATION ===
    initializeEventListeners();
    console.log('Review JS initialized successfully');
});