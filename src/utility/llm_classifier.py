"""
LLM Classifier for Ontology Selection

Uses OpenAI GPT to dynamically match tickets to appropriate ontologies.
"""

import json
import time
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from src.logging import logger
from src.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_TEMPERATURE
)


class LLMClassifier:
    """LLM-based ontology classification service"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        self.model = AZURE_OPENAI_DEPLOYMENT_NAME
        self.temperature = AZURE_OPENAI_TEMPERATURE
        logger.info(f"LLMClassifier initialized with Azure OpenAI model: {self.model}")
    
    def select_ontology(
        self,
        ticket_title: str,
        ticket_description: str,
        available_ontologies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Select the most appropriate ontology for a ticket using LLM.
        
        Args:
            ticket_title: Title of the ticket
            ticket_description: Description of the ticket
            available_ontologies: List of available ontology metadata
        
        Returns:
            Dict with ontology_id, confidence, reasoning, category, keywords
        """
        start_time = time.time()
        
        try:
            # Build ontology options description
            ontology_options = []
            for idx, ont in enumerate(available_ontologies):
                ontology_options.append({
                    "id": ont['ontology_id'],
                    "name": ont['name'],
                    "category": ont.get('category', 'general'),
                    "description": ont.get('description', ''),
                    "tags": ont.get('tags', [])
                })
            
            # Create prompt
            system_prompt = """You are an expert at matching IT tickets to appropriate data ontologies.
Analyze the ticket and select the most appropriate ontology based on the ticket's domain, category, and technical requirements.

Consider:
1. Technical domain (infrastructure, application, database, network, etc.)
2. Ticket type (incident, query, request, etc.)
3. Keywords and technical terms
4. Business context

Respond ONLY with valid JSON matching this structure:
{
    "ontology_id": <selected_ontology_id>,
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation>",
    "category": "<identified_category>",
    "keywords_found": ["<keyword1>", "<keyword2>"]
}"""
            
            user_prompt = f"""Ticket Information:
Title: {ticket_title}
Description: {ticket_description}

Available Ontologies:
{json.dumps(ontology_options, indent=2)}

Select the most appropriate ontology for this ticket."""
            
            logger.debug(f"Sending classification request to LLM with {len(available_ontologies)} ontologies")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Add metadata
            result['llm_model'] = self.model
            result['processing_time_ms'] = processing_time_ms
            
            logger.info(f"LLM selected ontology_id={result['ontology_id']} with confidence={result['confidence']}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"Response content: {content}")
            raise ValueError(f"LLM returned invalid JSON: {str(e)}")
        
        except Exception as e:
            logger.error(f"LLM classification error: {str(e)}")
            raise
    
    def validate_ontology_structure(self, ontology_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate ontology JSON structure for GraphRAG-SDK compatibility.
        
        Args:
            ontology_json: The ontology JSON to validate
        
        Returns:
            Dict with is_valid, errors, warnings
        """
        errors = []
        warnings = []
        
        # Check required top-level keys
        required_keys = ['entities', 'relationships']
        for key in required_keys:
            if key not in ontology_json:
                errors.append(f"Missing required key: '{key}'")
        
        # Validate entities structure
        if 'entities' in ontology_json:
            entities = ontology_json['entities']
            if not isinstance(entities, list):
                errors.append("'entities' must be an array")
            else:
                for idx, entity in enumerate(entities):
                    if not isinstance(entity, dict):
                        errors.append(f"Entity at index {idx} must be an object")
                    elif 'name' not in entity:
                        warnings.append(f"Entity at index {idx} missing 'name' field")
        
        # Validate relationships structure
        if 'relationships' in ontology_json:
            relationships = ontology_json['relationships']
            if not isinstance(relationships, list):
                errors.append("'relationships' must be an array")
            else:
                for idx, rel in enumerate(relationships):
                    if not isinstance(rel, dict):
                        errors.append(f"Relationship at index {idx} must be an object")
                    else:
                        for req_field in ['source', 'target', 'type']:
                            if req_field not in rel:
                                warnings.append(f"Relationship at index {idx} missing '{req_field}' field")
        
        is_valid = len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "entity_count": len(ontology_json.get('entities', [])),
            "relationship_count": len(ontology_json.get('relationships', []))
        }


# Singleton instance
llm_classifier = LLMClassifier()
