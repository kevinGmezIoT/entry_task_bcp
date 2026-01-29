import os
import json
import boto3
from django.core.management.base import BaseCommand
from core.models import PolicyDocument

class Command(BaseCommand):
    help = 'Ingests internal fraud policies into S3 to be used by Bedrock Knowledge Base'

    def handle(self, *args, **options):
        bucket_name = os.getenv("S3_POLICY_BUCKET")
        kb_id = os.getenv("BEDROCK_KB_ID")
        ds_id = os.getenv("BEDROCK_DS_ID")

        if not bucket_name:
            self.stderr.write("S3_POLICY_BUCKET environment variable not set")
            return

        self.stdout.write("Fetching policies from database...")
        policies = PolicyDocument.objects.all()
        
        # Bedrock KB works best with individual files or a consolidated JSONL/metadata approach.
        # Here we create a single JSON file that would ideally be matched with a metadata file,
        # but for simplicity, we'll upload each policy as a text file if there are few,
        # or a consolidated JSON.
        
        s3 = boto3.client('s3')
        
        for policy in policies:
            content = f"Policy ID: {policy.policy_id}\nVersion: {policy.version}\nRule: {policy.rule}"
            filename = f"policies/{policy.policy_id.replace(' ', '_')}.txt"
            
            self.stdout.write(f"Uploading {filename} to S3 bucket {bucket_name}...")
            s3.put_object(
                Bucket=bucket_name,
                Key=filename,
                Body=content,
                Metadata={
                    'policy_id': policy.policy_id,
                    'version': policy.version
                }
            )

        self.stdout.write(self.style.SUCCESS("Policies uploaded successfully to S3."))

        if kb_id and ds_id:
            self.stdout.write(f"Triggering sync for Knowledge Base {kb_id}...")
            bedrock_agent = boto3.client('bedrock-agent')
            try:
                bedrock_agent.start_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=ds_id
                )
                self.stdout.write(self.style.SUCCESS("Ingestion job started."))
            except Exception as e:
                self.stderr.write(f"Failed to start ingestion job: {str(e)}")
        else:
            self.stdout.write(self.style.WARNING("BEDROCK_KB_ID or BEDROCK_DS_ID not set. Skipping sync trigger."))
