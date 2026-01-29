from django.contrib import admin
from django.urls import path
from core.views import health, analyze_transaction

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("transactions/analyze/", analyze_transaction),
]
