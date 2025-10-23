// Pastikan kode ini dijalankan setelah DOM siap
$(document).ready(function() {

    // === TAMBAH REVIEW ===
    // Fungsi 'open' sekarang juga mengatur event-id di form
    window.openAddModal = function(eventId) {
        $('#addReviewForm').attr('data-event-id', eventId);
        $('#reviewAddModal').removeClass('hidden');
    }
    
    window.closeAddModal = function() {
        $('#reviewAddModal').addClass('hidden');
    }

    $('#addReviewForm').on('submit', function (e) {
        e.preventDefault();
        // Ambil eventId dari atribut data form-nya
        const eventId = $(this).attr('data-event-id'); 
        if (!eventId) {
            showToast('Error: Event ID not found', 'error');
            return;
        }
        const formData = $(this).serialize();

        $.post(`/review/${eventId}/create/`, formData)
            .done(res => {
                if (res.success) {
                    // Muat ulang list review agar konsisten dengan filter
                    // Ini lebih baik daripada prepend, 
                    // atau Anda bisa cek filter aktif
                    $('#filter-all').click(); // Asumsi memuat ulang semua
                    closeAddModal();
                    showToast('Review berhasil ditambahkan', 'success');
                    // Reset form
                    $('#addReviewForm')[0].reset();
                } else {
                    showToast(res.message || 'Gagal menambah review', 'error');
                }
            })
            .fail(() => showToast('Terjadi kesalahan server', 'error'));
    });

    // === EDIT REVIEW ===
    window.openEditModal = function(id, rating, komentar) {
        $('#edit-review-id').val(id);
        $('#edit-rating').val(rating);
        $('#edit-komentar').val(komentar);
        $('#reviewEditModal').removeClass('hidden');
    }

    window.closeEditModal = function() {
        $('#reviewEditModal').addClass('hidden');
    }

    $('#editReviewForm').on('submit', function (e) {
        e.preventDefault();
        const reviewId = $('#edit-review-id').val();
        const formData = $(this).serialize();

        $.post(`/review/${reviewId}/edit/`, formData)
            .done(res => {
                if (res.success) {
                    // Ganti card yang ada dengan HTML baru
                    $(`#review-${res.review_id}`).replaceWith(res.html);
                    closeEditModal();
                    showToast('Review berhasil diupdate', 'success');
                } else {
                    showToast('Gagal memperbarui review', 'error');
                }
            })
            .fail(() => showToast('Terjadi kesalahan server', 'error'));
    });

    // === DELETE REVIEW ===
    window.deleteReview = function(id) {
        if (!confirm('Are you sure to delete this review?')) return;
        
        $.post(`/review/${id}/delete/`, { csrfmiddlewaretoken: getCsrfToken() })
            .done(res => {
                if (res.success) {
                    $(`#review-${id}`).fadeOut(300, function() {
                        $(this).remove();
                    });
                    showToast('Review is deleted', 'success');
                } else {
                    showToast('Failed to delete review', 'error');
                }
            })
            .fail(() => showToast('Terjadi kesalahan server', 'error'));
    }

    // === FILTER REVIEW ===
    $('#filter-all, #filter-my').on('click', function () {
        const filter = $(this).data('filter');
        const eventId = $('#review-list-container').data('event-id');

        // Atur style tombol aktif/non-aktif
        if (filter === 'my') {
            $('#filter-my').removeClass('bg-gray-200 text-[#537FB9]').addClass('bg-[#537FB9] text-white');
            $('#filter-all').removeClass('bg-[#537FB9] text-white').addClass('bg-gray-200 text-[#537FB9]');
        } else {
            $('#filter-all').removeClass('bg-gray-200 text-[#537FB9]').addClass('bg-[#537FB9] text-white');
            $('#filter-my').removeClass('bg-[#537FB9] text-white').addClass('bg-gray-200 text-[#537FB9]');
        }

        $.get(`/review/${eventId}/filter/?type=${filter}`)
            .done(res => {
                $('#review-list-container').html(res.html);
                // Tidak perlu toast untuk filter, pergantian tombol sudah cukup
            })
            .fail(() => showToast('Gagal memuat review', 'error'));
    });

    // === HELPERS ===
    function getCsrfToken() {
        return $('input[name="csrfmiddlewaretoken"]').val();
    }

    window.showToast = function(msg, type = 'success') {
        const color = type === 'error' ? 'bg-red-500' : 'bg-[#537FB9]';
        const toast = $(`<div class="${color} text-white px-4 py-2 rounded-xl fixed bottom-5 right-5 shadow-md font-[Kanit] opacity-0 transition-opacity" style="z-index: 100;">${msg}</div>`);
        $('body').append(toast);
        setTimeout(() => toast.css('opacity', '1'), 100);
        setTimeout(() => toast.css('opacity', '0'), 2500);
        setTimeout(() => toast.remove(), 3000);
    }

}); // Akhir dari $(document).ready