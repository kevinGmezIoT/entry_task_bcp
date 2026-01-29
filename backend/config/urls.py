from django.contrib import admin
from django.urls import path
from core.views import (
    health, analyze_transaction, get_transaction_detail, 
    list_hitl_cases, resolve_hitl_case, seed_batch, 
    create_manual_transaction, get_audit_reports
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("transactions/analyze/", analyze_transaction),
    path("transactions/seed/", seed_batch),
    path("transactions/create/", create_manual_transaction),
    path("transactions/<str:transaction_id>/", get_transaction_detail),
    path("hitl/cases/", list_hitl_cases),
    path("hitl/cases/<int:case_id>/resolve/", resolve_hitl_case),
    path("reports/", get_audit_reports),
]
