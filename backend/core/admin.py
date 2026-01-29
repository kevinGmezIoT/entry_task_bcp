from django.contrib import admin
from core.models import CustomerProfile, Transaction, PolicyDocument, DecisionRecord, AuditEvent, HumanReviewCase

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'usual_amount_avg', 'usual_countries')
    search_fields = ('customer_id',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'customer', 'amount', 'country', 'timestamp')
    list_filter = ('country', 'channel')
    search_fields = ('transaction_id', 'customer__customer_id')

@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ('policy_id', 'version')
    search_fields = ('policy_id', 'rule')

@admin.register(DecisionRecord)
class DecisionRecordAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'decision', 'confidence', 'created_at')
    list_filter = ('decision',)
    search_fields = ('transaction__transaction_id',)

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'transaction', 'timestamp')
    list_filter = ('event_type',)

@admin.register(HumanReviewCase)
class HumanReviewCaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'status', 'assigned_to', 'created_at')
    list_filter = ('status',)
    search_fields = ('transaction__transaction_id',)
    actions = ['mark_as_resolved']

    def mark_as_resolved(self, request, queryset):
        queryset.update(status='RESOLVED')
    mark_as_resolved.short_description = "Marcar seleccionados como Resueltos"
