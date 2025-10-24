function showToast({title = "Info", message = "", type = "info", icon = ""}) {
    const toast = document.getElementById("toast-main");
    const toastTitle = document.getElementById("toast-title");
    const toastMsg = document.getElementById("toast-message");
    const toastIcon = document.getElementById("toast-icon");

    // Pilih icon default jika tidak ada
    if (!icon) {
        if (type === "success") icon = "✅";
        else if (type === "error") icon = "❌";
        else if (type === "warning") icon = "⚠️";
        else icon = "ℹ️";
    }

    toastTitle.textContent = title;
    toastMsg.textContent = message;
    toastIcon.textContent = icon;

    // Ganti warna border sesuai tipe
    toast.classList.remove("border-gray-300", "border-green-400", "border-red-400", "border-yellow-400", "border-blue-400");
    if (type === "success") toast.classList.add("border-green-400");
    else if (type === "error") toast.classList.add("border-red-400");
    else if (type === "warning") toast.classList.add("border-yellow-400");
    else toast.classList.add("border-blue-400");

    // Tampilkan toast
    toast.classList.remove("opacity-0", "pointer-events-none", "translate-y-10");
    toast.classList.add("opacity-100", "translate-y-0");

    // Fungsi untuk menyembunyikan toast
    function hideToast() {
        toast.classList.remove("opacity-100", "translate-y-0");
        toast.classList.add("opacity-0", "pointer-events-none", "translate-y-10");
    }

    // Pasang event close setiap kali toast muncul
    const closeBtn = document.getElementById("toast-close-btn");
    if (closeBtn) {
        closeBtn.onclick = hideToast;
    }

    // Auto hide setelah 3 detik
    setTimeout(hideToast, 3000);
}