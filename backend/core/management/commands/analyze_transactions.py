from django.core.management.base import BaseCommand
from core.models import Transaction, DecisionRecord
from core.services import DecisionService

class Command(BaseCommand):
    help = 'Analyzes all transactions and generates decisions based on signals'

    def handle(self, *args, **options):
        transactions = Transaction.objects.all()
        if not transactions.exists():
            self.stdout.write(self.style.WARNING('No transactions found in the database. Please run seed_data first.'))
            return

        self.stdout.write(f'Analyzing {transactions.count()} transactions...')

        for tx in transactions:
            record = DecisionService.apply_decision(tx)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Analyzed Tx: {tx.transaction_id} | Decision: {record.decision} | Confidence: {record.confidence:.2f}'
                )
            )
            if record.signals:
                self.stdout.write(f'  Signals: {", ".join(record.signals)}')
            
        self.stdout.write(self.style.SUCCESS('Analysis complete.'))
