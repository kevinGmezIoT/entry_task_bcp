import boto3
import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("agents-flask.rag")

class AWSRAGService:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.kb_id = os.getenv("BEDROCK_KB_ID")
        self.client = boto3.client("bedrock-agent-runtime", region_name=self.region)
        
        # Load local policies for metadata recovery
        self.policies_map = []
        try:
            # Try to find data/fraud_policies.json in the parent directory
            base_dir = Path(__file__).resolve().parent.parent
            policies_path = base_dir / "data" / "fraud_policies.json"
            if policies_path.exists():
                with open(policies_path, "r", encoding="utf-8") as f:
                    self.policies_map = json.load(f)
                logger.info(f"Loaded {len(self.policies_map)} policies for metadata recovery.")
        except Exception as e:
            logger.warning(f"Could not load local policies for metadata recovery: {e}")

    def query_policies(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the Amazon Bedrock Knowledge Base for relevant fraud policies.
        """
        if not self.kb_id:
            logger.warning("BEDROCK_KB_ID not set. Returning mock data for RAG.")
            return [
                {
                    "policy_id": "FP-01",
                    "chunk_id": "0",
                    "version": "2025.1",
                    "rule": f"Mock policy for query: {query}"
                }
            ]

        try:
            response = self.client.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )

            results = []
            for i, retrieval in enumerate(response.get('retrievalResults', [])):
                metadata = retrieval.get('metadata', {})
                text = retrieval.get('content', {}).get('text', '')
                
                policy_id = metadata.get('policy_id', 'UNKNOWN')
                version = metadata.get('version', 'latest')
                
                # Metadata Recovery Logic: If unknown, try to match text with local policies
                if policy_id == 'UNKNOWN' and self.policies_map:
                    for p in self.policies_map:
                        # If the retrieved text is in the rule or vice versa
                        # Or if we have a high overlap
                        if p['rule'] in text or text in p['rule']:
                            policy_id = p['policy_id']
                            version = p['version']
                            break
                
                results.append({
                    "policy_id": policy_id,
                    "chunk_id": str(i),
                    "version": version,
                    "rule": text  # Changed from 'text' to 'rule' for frontend compatibility
                })
            
            return results

        except Exception as e:
            logger.error(f"Error querying Bedrock Knowledge Base: {str(e)}")
            return []

# Singleton instance
rag_service = AWSRAGService()
