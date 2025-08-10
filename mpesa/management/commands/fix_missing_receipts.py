"""
Django Management Command: Fix Missing Receipt Numbers

This command queries M-Pesa API to retrieve receipt numbers for completed
transactions that don't have receipt numbers due to incomplete callbacks.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from mpesa.models import Transaction
from mpesa.stk_push import MpesaGateWay
import time


class Command(BaseCommand):
    help = 'Fix completed transactions that are missing receipt numbers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days back to check for transactions (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of transactions to process (default: 50)'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        limit = options['limit']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🔍 Scanning for completed transactions missing receipt numbers...'
            )
        )
        
        # Find completed transactions without receipt numbers in the last N days
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        missing_receipts = Transaction.objects.filter(
            status="0",  # Completed
            receipt_no__isnull=True,  # Missing receipt
            created__gte=cutoff_date  # Within date range
        ).order_by('-created')[:limit]
        
        if not missing_receipts.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ No completed transactions missing receipt numbers found!'
                )
            )
            return
            
        self.stdout.write(
            f'Found {missing_receipts.count()} transactions missing receipt numbers'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN - No changes will be made')
            )
        
        # Initialize M-Pesa gateway
        try:
            gateway = MpesaGateWay()
        except Exception as e:
            raise CommandError(f'Failed to initialize M-Pesa gateway: {e}')
        
        fixed_count = 0
        failed_count = 0
        
        for transaction in missing_receipts:
            self.stdout.write(f'\n📋 Processing transaction {transaction.transaction_no}')
            self.stdout.write(f'   Checkout ID: {transaction.checkout_request_id}')
            self.stdout.write(f'   Amount: {transaction.amount}')
            self.stdout.write(f'   Created: {transaction.created}')
            
            try:
                # Query M-Pesa for transaction details
                self.stdout.write('   🔍 Querying M-Pesa API...')
                
                query_result = gateway.stk_push_query(transaction.checkout_request_id)
                
                if (query_result and 
                    isinstance(query_result, dict) and 
                    query_result.get('ResultCode') == '0'):
                    
                    # Check if we have local transaction data with receipt
                    if ('local_transaction' in query_result and 
                        query_result['local_transaction'].get('receipt_no')):
                        
                        receipt_no = query_result['local_transaction']['receipt_no']
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✅ Found receipt: {receipt_no}')
                        )
                        
                        if not dry_run:
                            transaction.receipt_no = receipt_no
                            transaction.save(update_fields=['receipt_no'])
                            self.stdout.write('   💾 Receipt number saved!')
                        else:
                            self.stdout.write('   🧪 Would save receipt number')
                            
                        fixed_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING('   ⚠️  Query successful but no receipt found')
                        )
                        failed_count += 1
                else:
                    result_code = query_result.get('ResultCode', 'Unknown') if query_result else 'No response'
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Query failed - Result: {result_code}')
                    )
                    failed_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error querying transaction: {e}')
                )
                failed_count += 1
            
            # Add small delay to respect rate limits
            time.sleep(0.5)
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Transactions processed: {missing_receipts.count()}')
        self.stdout.write(self.style.SUCCESS(f'Successfully fixed: {fixed_count}'))
        self.stdout.write(self.style.ERROR(f'Failed to fix: {failed_count}'))
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n🧪 This was a dry run - no changes were made')
            )
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Fixed {fixed_count} transactions!')
            )
