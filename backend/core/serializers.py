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
    class Meta:
        model = DecisionRecord
        fields = '__all__'

class HumanReviewCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanReviewCase
        fields = '__all__'
