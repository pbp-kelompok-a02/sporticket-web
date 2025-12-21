# order/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Order
from ticket.models import Ticket
from django.http import JsonResponse
import json



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



@csrf_exempt
@login_required
def create_order_flutter(request, ticket_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    quantity = int(data.get("quantity", 0))
    status_str = data.get("status")

    if quantity <= 0 or status_str not in ["confirmed", "pending"]:
        return JsonResponse({"success": False, "error": "Bad request"}, status=400)

    ticket = get_object_or_404(Ticket, pk=ticket_id)

    with transaction.atomic():
        ticket.refresh_from_db()

        if quantity > ticket.stock:
            return JsonResponse(
                {"success": False, "error": f"Stock insufficient. Left: {ticket.stock}"},
                status=400
            )

        status = (
            Order.STATUS_CONFIRMED
            if status_str == "confirmed"
            else Order.STATUS_PENDING
        )

        order = Order.objects.create(
            user=request.user,
            ticket=ticket,
            quantity=quantity,
            status=status,
            harga=ticket.price * quantity,
        )

        if status == Order.STATUS_CONFIRMED:
            ticket.stock -= quantity
            ticket.save(update_fields=["stock"])

    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "remaining_stock": ticket.stock,
    })




@login_required
def order_history_flutter(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .select_related("ticket", "ticket__event")
        .order_by("-created_at")
    )

    data = [{
        "order_id": o.id,
        "ticket_id": str(o.ticket.id),
        "event_id": str(o.ticket.event.id),
        "event_name": o.ticket.event.name,
        "quantity": o.quantity,
        "seating": o.ticket.category,
        "price": float(o.harga),
        "status": o.status,
        "ticket_stock": o.ticket.stock,
        "ticket_price": float(o.ticket.price),
    } for o in orders]

    return JsonResponse(data, safe=False)




@csrf_exempt
@login_required
def edit_order_flutter(request, order_id):

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Invalid method"},
            status=405
        )

    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if order.status != Order.STATUS_PENDING:
        return JsonResponse(
            {"success": False, "error": "Only pending orders can be edited"},
            status=400
        )

    try:
        data = json.loads(request.body)
        new_quantity = int(data["quantity"])
        new_ticket_id = data["ticket_id"]
        new_status = data.get("status")  # 👈 ADD THIS

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": "Invalid payload"},
            status=400
        )

    if new_quantity <= 0:
        return JsonResponse(
            {"success": False, "error": "Quantity must be > 0"},
            status=400
        )

    old_ticket = order.ticket
    old_quantity = order.quantity

    new_ticket = get_object_or_404(Ticket, pk=new_ticket_id)

    with transaction.atomic():
        # 1️⃣ restore old stock
        old_ticket.stock += old_quantity
        old_ticket.save(update_fields=["stock"])

        # 2️⃣ check new stock
        if new_quantity > new_ticket.stock:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Stock insufficient. Only {new_ticket.stock} left"
                },
                status=400
            )

        # 3️⃣ deduct new stock
        new_ticket.save(update_fields=["stock"])

        # 4️⃣ update order
        order.ticket = new_ticket
        order.quantity = new_quantity
        order.harga = new_ticket.price * new_quantity

        if new_status == "confirmed":
            order.status = Order.STATUS_CONFIRMED

        order.save()


    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "new_ticket": str(new_ticket.id),
        "new_quantity": new_quantity,
        "remaining_stock": new_ticket.stock,
    })



@login_required
def order_detail_flutter(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    return JsonResponse({
        "order_id": order.id,
        "ticket_id": str(order.ticket.id),
        "event_name": order.ticket.event.name,
        "category": order.ticket.category,
        "quantity": order.quantity,
        "ticket_price": float(order.ticket.price),
        "ticket_stock": order.ticket.stock,
        "status": order.status,
    })


@csrf_exempt
@login_required
def confirm_order_flutter(request, order_id):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Invalid method"},
            status=405
        )

    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if order.status != Order.STATUS_PENDING:
        return JsonResponse(
            {"success": False, "error": "Order already confirmed"},
            status=400
        )

    ticket = order.ticket
    quantity = order.quantity

    # check stock
    if quantity > ticket.stock:
        return JsonResponse(
            {
                "success": False,
                "error": f"Stock insufficient. Only {ticket.stock} left"
            },
            status=400
        )

    with transaction.atomic():
        ticket.stock -= quantity
        ticket.save(update_fields=["stock"])

        order.status = Order.STATUS_CONFIRMED
        order.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "remaining_stock": ticket.stock,
    })

@csrf_exempt
@login_required
def cancel_order_flutter(request, order_id):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Invalid method"},
            status=405
        )

    order = get_object_or_404(Order, pk=order_id, user=request.user)

    # ❗ Only pending orders can be cancelled
    if order.status != Order.STATUS_PENDING:
        return JsonResponse(
            {"success": False, "error": "Only pending orders can be cancelled"},
            status=400
        )

    with transaction.atomic():
        # restore stock
        ticket = order.ticket
        ticket.save(update_fields=["stock"])

        # cancel order
        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "status": order.status,
        "restored_stock": ticket.stock,
    })
