import csv
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import CustomerProfile, Transaction, PolicyDocument
from django.utils import timezone
from django.utils.dateparse import parse_datetime

class Command(BaseCommand):
    help = 'Seeds the database with fraud policies and example data'

    def handle(self, *args, **options):
        data_dir = os.path.join(settings.BASE_DIR, '..', 'data')
        
        # 1. Ingest Fraud Policies
        policies_path = os.path.join(data_dir, 'fraud_policies.json')
        if os.path.exists(policies_path):
            with open(policies_path, 'r', encoding='utf-8') as f:
                policies = json.load(f)
                for p in policies:
                    obj, created = PolicyDocument.objects.update_or_create(
                        policy_id=p['policy_id'],
                        defaults={
                            'rule': p['rule'],
                            'version': p['version']
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Policy {p["policy_id"]} {"created" if created else "updated"}'))
        
        # 2. Seed Customer Behavior
        behavior_path = os.path.join(data_dir, 'customer_behavior.csv')
        if os.path.exists(behavior_path):
            with open(behavior_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    obj, created = CustomerProfile.objects.update_or_create(
                        customer_id=row['customer_id'],
                        defaults={
                            'usual_amount_avg': row['usual_amount_avg'],
                            'usual_hours': row['usual_hours'],
                            'usual_countries': row['usual_countries'],
                            'usual_devices': row['usual_devices']
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Customer {row["customer_id"]} {"created" if created else "updated"}'))

        # 3. Seed Example Transactions
        transactions_path = os.path.join(data_dir, 'transactions.csv')
        if os.path.exists(transactions_path):
            with open(transactions_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Ensure customer exists
                    customer, _ = CustomerProfile.objects.get_or_create(customer_id=row['customer_id'], defaults={
                        'usual_amount_avg': 0,
                        'usual_hours': '',
                        'usual_countries': '',
                        'usual_devices': ''
                    })
                    
                    dt = parse_datetime(row['timestamp'])
                    if dt and timezone.is_naive(dt):
                        dt = timezone.make_aware(dt)

                    obj, created = Transaction.objects.update_or_create(
                        transaction_id=row['transaction_id'],
                        defaults={
                            'customer': customer,
                            'amount': row['amount'],
                            'currency': row['currency'],
                            'country': row['country'],
                            'channel': row['channel'],
                            'device_id': row['device_id'],
                            'timestamp': dt,
                            'merchant_id': row['merchant_id']
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Transaction {row["transaction_id"]} {"created" if created else "updated"}'))

