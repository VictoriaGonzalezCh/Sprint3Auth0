from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    path("admin/", admin.site.urls),

    # Home -> lista de pedidos
    path("", views.index, name="home"),

    # Login Auth0
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),

    # 🔹 Logout propio (nombre único)
    path("logout/", views.logout_view, name="custom_logout"),

    # Auth0 / social auth
    path("", include("social_django.urls")),

    # Pedidos
    path("orders/", include("orders.urls")),

    # Apps originales
    path("", include("measurements.urls")),
    path("", include("variables.urls")),
]
