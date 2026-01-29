from django.contrib import admin
from django.urls import path
from core.views import (
    health, analyze_transaction, get_transaction_detail, 
    list_hitl_cases, resolve_hitl_case, seed_batch, 
    create_manual_transaction, get_audit_reports, download_report
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/transactions/analyze/", analyze_transaction),
    path("api/transactions/seed/", seed_batch),
    path("api/transactions/create/", create_manual_transaction),
    path("api/transactions/<str:transaction_id>/", get_transaction_detail),
    path("api/hitl/cases/", list_hitl_cases),
    path("api/hitl/cases/<int:case_id>/resolve/", resolve_hitl_case),
    path("api/reports/", get_audit_reports),
    path("api/reports/<str:transaction_id>/pdf/", download_report),
]
