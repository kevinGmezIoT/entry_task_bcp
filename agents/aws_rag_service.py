import boto3
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("agents-flask.rag")

class AWSRAGService:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.kb_id = os.getenv("BEDROCK_KB_ID")
        self.client = boto3.client("bedrock-agent-runtime", region_name=self.region)

    def query_policies(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the Amazon Bedrock Knowledge Base for relevant fraud policies.
        """
        if not self.kb_id:
            logger.warning("BEDROCK_KB_ID not set. Returning mock data for RAG.")
            return [
                {
                    "policy_id": "MOCK-01",
                    "chunk_id": "0",
                    "version": "1.0",
                    "text": f"Mock policy for query: {query}"
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
                # Bedrock KB metadata is stored in 'metadata' dictionary
                metadata = retrieval.get('metadata', {})
                results.append({
                    "policy_id": metadata.get('policy_id', 'UNKNOWN'),
                    "chunk_id": str(i),
                    "version": metadata.get('version', 'latest'),
                    "text": retrieval.get('content', {}).get('text', '')
                })
            
            return results

        except Exception as e:
            logger.error(f"Error querying Bedrock Knowledge Base: {str(e)}")
            return []

# Singleton instance
rag_service = AWSRAGService()
