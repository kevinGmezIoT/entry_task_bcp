from rest_framework import serializers
from core.models import Transaction, CustomerProfile, DecisionRecord, HumanReviewCase

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class DecisionRecordSerializer(serializers.ModelSerializer):
    transaction_id = serializers.ReadOnlyField(source='transaction.transaction_id')
    
    class Meta:
        model = DecisionRecord
        fields = [
            'id',
            'transaction_id',
            'decision', 
            'confidence', 
            'signals', 
            'citations_internal', 
            'citations_external', 
            'explanation_customer', 
            'explanation_audit',
            'created_at'
        ]

class HumanReviewCaseSerializer(serializers.ModelSerializer):
    transaction = TransactionSerializer(read_only=True)
    
    class Meta:
        model = HumanReviewCase
        fields = [
            'id',
            'transaction',
            'status',
            'assigned_to',
            'human_decision',
            'notes',
            'created_at',
            'resolved_at'
        ]
