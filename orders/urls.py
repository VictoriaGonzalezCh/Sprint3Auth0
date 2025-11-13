from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.orders_list, name="list"),
    path("<int:order_id>/editar/", views.order_edit, name="edit"),
]

