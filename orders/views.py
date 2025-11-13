import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Order


def _get_user_role(user):
    """
    Regla simple para el experimento:
    - Si el username o el email contienen 'jefe' o 'admin' -> JEFE_LOGISTICA
    - En cualquier otro caso -> OPERARIO
    """
    username = (user.username or "").lower()
    email = (getattr(user, "email", "") or "").lower()

    if "jefe" in username or "admin" in username or "jefe" in email:
        return "JEFE_LOGISTICA"
    return "OPERARIO"


@login_required
def orders_list(request):
    orders = Order.objects.all().order_by("id")
    last_update_time_ms = request.session.pop("last_update_time_ms", None)
    role = _get_user_role(request.user)

    context = {
        "orders": orders,
        "last_update_time_ms": last_update_time_ms,
        "role": role,
    }
    return render(request, "orders/orders_list.html", context)


@login_required
def order_edit(request, order_id):
    start = time.time()
    order = get_object_or_404(Order, pk=order_id)
    role = _get_user_role(request.user)

    # 🔒 Control de autorización:
    # Solo el JEFE_LOGISTICA puede modificar pedidos.
    if role != "JEFE_LOGISTICA":
        response_time_ms = (time.time() - start) * 1000.0
        context = {
            "order": order,
            "role": role,
            "response_time_ms": response_time_ms,
        }
        return render(request, "orders/unauthorized.html", context)

    # Si llega aquí es porque SÍ está autorizado
    if request.method == "POST":
        order.quantity = int(request.POST.get("quantity", order.quantity))
        order.products_list = request.POST.get("products_list", order.products_list)
        order.picker_name = request.POST.get("picker_name", order.picker_name)
        order.status = request.POST.get("status", order.status)
        order.save()

        response_time_ms = (time.time() - start) * 1000.0
        # Guardamos el tiempo en sesión para mostrarlo en la lista
        request.session["last_update_time_ms"] = response_time_ms

        return redirect("orders:list")

    # GET autorizado: solo muestra el formulario y tiempo de respuesta
    response_time_ms = (time.time() - start) * 1000.0
    context = {
        "order": order,
        "role": role,
        "response_time_ms": response_time_ms,
    }
    return render(request, "orders/order_edit.html", context)
