"""
LLM client for Ollama API communication.

This module handles communication with Ollama server
for text generation using llama3 model.
"""

import logging
import requests
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for Ollama LLM API."""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        temperature: float = 0.2,
        timeout: int = 30
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server base URL
            model: Model name to use
            temperature: Sampling temperature
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.generate_endpoint = f"{self.base_url}/api/generate"
        
        logger.info(f"Initialized Ollama client with model={model}, temperature={temperature}")
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Ollama API.
        
        Args:
            prompt: Input prompt for generation
            
        Returns:
            Generated text response
            
        Raises:
            requests.RequestException: If API request fails
            json.JSONDecodeError: If response parsing fails
        """
        logger.info(f"Sending request to Ollama API with prompt length: {len(prompt)}")
        
        request_data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(
                self.generate_endpoint,
                json=request_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            logger.info(f"Received response with length: {len(generated_text)}")
            
            return generated_text
            
        except requests.exceptions.Timeout:
            logger.error(f"Request to Ollama API timed out after {self.timeout}s")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama server at {self.base_url}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from Ollama API: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama API response: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Ollama client: {e}")
            raise
    
    def check_connection(self) -> bool:
        """
        Check if Ollama server is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to connect to Ollama server: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the client configuration.
        
        Returns:
            Dictionary with client configuration
        """
        return {
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "endpoint": self.generate_endpoint
        }
