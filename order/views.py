# order/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Order
from ticket.models import Ticket
from django.http import JsonResponse


@login_required
def create_order(request, ticket_id, order_id=None):
    """
    Bisa create order baru atau edit order lama (kalau order_id dikirim).
    - Tombol Purchase -> status confirmed (stok berkurang).
    - Tombol Save Ticket -> status pending (stok tidak berkurang).
    """
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    order = None

    if order_id:  # kalau edit
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        if not order.can_modify():
            return redirect("order:history")

    if request.method == "POST":
        print("POST DATA:", request.POST)
        try:
            quantity = int(request.POST.get("quantity", 0))
        except (TypeError, ValueError):
            return render(request, "order/create_order.html", {
                "ticket": ticket,
                "order": order,
                "error_message": "Jumlah tiket tidak valid."
            })
        
        chosen_ticket_id = request.POST.get("ticket_id")
        action = request.POST.get("action")  # "purchase" atau "pending"

        chosen_ticket = get_object_or_404(Ticket, pk=chosen_ticket_id)

        if quantity <= 0:
            return render(request, "order/create_order.html", {
                "ticket": ticket,
                "order": order,
                "error_message": "Jumlah tiket tidak valid."
            })

        try:
            with transaction.atomic():
                chosen_ticket.refresh_from_db()

                if quantity > chosen_ticket.stock:
                    return render(request, "order/create_order.html", {
                        "ticket": ticket,
                        "order": order,
                        "error_message": f"Stok tidak mencukupi. Tersisa {chosen_ticket.stock}."
                    })

                # Tentukan status berdasarkan tombol
                status = Order.STATUS_CONFIRMED if action == "purchase" else Order.STATUS_PENDING

                if order:  # update existing order
                    order.ticket = chosen_ticket
                    order.quantity = quantity
                    order.status = status
                    order.harga = chosen_ticket.price * quantity
                    order.save()
                else:  # create new order
                    order = Order.objects.create(
                        user=request.user,
                        ticket=chosen_ticket,
                        quantity=quantity,
                        status=status,
                        harga=chosen_ticket.price * quantity,
                    )

                # Kalau purchase -> stok langsung berkurang
                if status == Order.STATUS_CONFIRMED:
                    chosen_ticket.stock -= quantity
                    chosen_ticket.save(update_fields=["stock"])

        except Exception as e:
            return render(request, "order/create_order.html", {
                "ticket": ticket,
                "order": order,
                "error_message": f"Terjadi error: {e}"
            })

        # setelah berhasil → langsung ke history
        return redirect("order:history")
    
    return render(request, "order/create_order.html", {"ticket": ticket, "order": order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.status in [Order.STATUS_PENDING, Order.STATUS_CONFIRMED]:
        order.cancel()
    return redirect("order:history")

@login_required
def cancel_order_ajax(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        if order.status in [Order.STATUS_PENDING, Order.STATUS_CONFIRMED]:
            order.cancel()
            return JsonResponse({"success": True, "status": "cancelled"})
        return JsonResponse({"success": False, "error": "Order cannot be cancelled."}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

# INI YANG BENER KODENYA
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).select_related("ticket", "ticket__event")

    status = request.GET.get("status")
    if status:
        orders = orders.filter(status=status)

    return render(request, "order/history.html", {"orders": orders})


# Testing
# def order_history(request):
#     orders = Order.objects.all().select_related("ticket", "ticket__event")
#     return render(request, "order/history.html", {"orders": orders})