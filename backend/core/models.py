from django.db import models
from django.utils import timezone

class CustomerProfile(models.Model):
    customer_id = models.CharField(max_length=50, unique=True)
    usual_amount_avg = models.DecimalField(max_digits=15, decimal_places=2)
    usual_hours = models.CharField(max_length=50)  # e.g., "08-20"
    usual_countries = models.CharField(max_length=100)  # comma separated or JSON
    usual_devices = models.CharField(max_length=255)  # comma separated or JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.customer_id

class Transaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10)
    country = models.CharField(max_length=50)
    channel = models.CharField(max_length=50)
    device_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    merchant_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id

class PolicyDocument(models.Model):
    policy_id = models.CharField(max_length=50, unique=True)
    rule = models.TextField()
    version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.policy_id} (v{self.version})"

class DecisionRecord(models.Model):
    DECISION_CHOICES = [
        ('APPROVE', 'APPROVE'),
        ('CHALLENGE', 'CHALLENGE'),
        ('BLOCK', 'BLOCK'),
        ('ESCALATE_TO_HUMAN', 'ESCALATE_TO_HUMAN'),
    ]
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='decision')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    confidence = models.FloatField()
    signals = models.JSONField(default=list)
    citations_internal = models.JSONField(default=list)
    citations_external = models.JSONField(default=list)
    explanation_customer = models.TextField()
    explanation_audit = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.decision}"

class AuditEvent(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='audit_trail', null=True, blank=True)
    event_type = models.CharField(max_length=100)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"

class HumanReviewCase(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'OPEN'),
        ('IN_PROGRESS', 'IN_PROGRESS'),
        ('RESOLVED', 'RESOLVED'),
        ('CLOSED', 'CLOSED'),
    ]
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='review_cases')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    assigned_to = models.CharField(max_length=100, null=True, blank=True)
    human_decision = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Case {self.id} - {self.status}"
