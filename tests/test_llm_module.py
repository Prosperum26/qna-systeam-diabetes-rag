#!/usr/bin/env python3
"""
Test script for LLM module.

This script tests the LLM module independently by sending
mock RAG prompts to Ollama and measuring response times.
"""

import sys
import time
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm import RAGGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_mock_diabetes_context() -> str:
    """
    Create mock diabetes-related context to simulate retrieved documents.
    
    Returns:
        Formatted context string with diabetes information
    """
    context = """----- Document 1 -----
Title: Diabetes Overview
Section: Introduction

Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels. It occurs when the body either doesn't produce enough insulin or can't effectively use the insulin it produces. There are three main types of diabetes: Type 1, Type 2, and gestational diabetes.

----- Document 2 -----
Title: Type 2 Diabetes
Section: Symptoms and Diagnosis

Common symptoms of Type 2 diabetes include increased thirst, frequent urination, unexplained weight loss, fatigue, blurred vision, and slow-healing sores. Diagnosis is typically made through blood tests including fasting blood glucose, oral glucose tolerance test, and A1C test.

----- Document 3 -----
Title: Diabetes Management
Section: Treatment Options

Treatment for Type 2 diabetes often begins with lifestyle modifications including diet changes, regular exercise, and weight management. If these measures are insufficient, oral medications such as metformin may be prescribed. In some cases, insulin therapy may be required to achieve adequate blood glucose control."""
    
    return context

def create_mock_chunks():
    """
    Create mock chunk data to simulate retriever output.
    
    Returns:
        List of chunk dictionaries with metadata
    """
    chunks = [
        {
            "chunk_id": "chunk_1",
            "doc_id": "diabetes_overview",
            "title": "Diabetes Overview",
            "heading": "Introduction",
            "text": "Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels. It occurs when the body either doesn't produce enough insulin or can't effectively use the insulin it produces. There are three main types of diabetes: Type 1, Type 2, and gestational diabetes.",
            "position": 0,
            "token_count": 45
        },
        {
            "chunk_id": "chunk_2", 
            "doc_id": "type2_diabetes",
            "title": "Type 2 Diabetes",
            "heading": "Symptoms and Diagnosis",
            "text": "Common symptoms of Type 2 diabetes include increased thirst, frequent urination, unexplained weight loss, fatigue, blurred vision, and slow-healing sores. Diagnosis is typically made through blood tests including fasting blood glucose, oral glucose tolerance test, and A1C test.",
            "position": 0,
            "token_count": 52
        },
        {
            "chunk_id": "chunk_3",
            "doc_id": "diabetes_management", 
            "title": "Diabetes Management",
            "heading": "Treatment Options",
            "text": "Treatment for Type 2 diabetes often begins with lifestyle modifications including diet changes, regular exercise, and weight management. If these measures are insufficient, oral medications such as metformin may be prescribed. In some cases, insulin therapy may be required to achieve adequate blood glucose control.",
            "position": 0,
            "token_count": 58
        }
    ]
    
    return chunks

def test_llm_module():
    """
    Test the LLM module with mock RAG data.
    
    This function simulates a complete RAG flow:
    1. Mock retrieved chunks (normally from retriever)
    2. Build context from chunks
    3. Generate answer using LLM
    4. Measure and log performance
    """
    logger.info("Starting LLM module test")
    
    try:
        # Step 1: Initialize the LLM generator
        logger.info("Initializing RAG generator...")
        generator = RAGGenerator(
            ollama_base_url="http://localhost:11434",
            model="llama3",
            temperature=0.2,
            max_context_tokens=1500
        )
        
        # Step 2: Check if Ollama server is available
        logger.info("Checking Ollama server connection...")
        health = generator.check_system_health()
        
        if not health["ollama_connected"]:
            logger.error("Ollama server is not running or not accessible")
            logger.info("Please start Ollama server with: ollama serve")
            logger.info("And ensure llama3 model is pulled with: ollama pull llama3")
            return False
        
        logger.info(f"Ollama server connected successfully with model: {health['model']}")
        
        # Step 3: Create mock data (simulating retriever output)
        logger.info("Creating mock diabetes-related context...")
        mock_chunks = create_mock_chunks()
        test_question = "What are the common symptoms of Type 2 diabetes and how is it diagnosed?"
        
        logger.info(f"Test question: {test_question}")
        logger.info(f"Number of mock chunks: {len(mock_chunks)}")
        
        # Step 4: Generate answer (this simulates the complete RAG pipeline)
        logger.info("Sending prompt to LLM...")
        start_time = time.time()
        
        response = generator.generate_answer(
            query=test_question,
            chunks=mock_chunks
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Step 5: Display results
        logger.info("=== LLM Response ===")
        print(f"\n{'='*50}")
        print("QUESTION:")
        print(test_question)
        print(f"\n{'='*50}")
        print("GENERATED ANSWER:")
        print(response.answer)
        print(f"\n{'='*50}")
        print("SOURCES:")
        for source in response.sources:
            print(f"- {source}")
        print(f"\n{'='*50}")
        print("PERFORMANCE METRICS:")
        print(f"Response time: {response_time:.2f} seconds")
        print(f"Chunks used: {response.chunk_count}")
        print(f"Context tokens: {response.context_tokens}")
        print(f"Answer length: {len(response.answer)} characters")
        print(f"{'='*50}\n")
        
        # Step 6: Log performance metrics
        logger.info(f"Test completed successfully")
        logger.info(f"Response time: {response_time:.2f}s")
        logger.info(f"Answer length: {len(response.answer)} chars")
        logger.info(f"Sources found: {len(response.sources)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during LLM module test: {e}")
        logger.error("Please ensure:")
        logger.error("1. Ollama server is running: ollama serve")
        logger.error("2. Llama3 model is available: ollama pull llama3")
        logger.error("3. Server is accessible at http://localhost:11434")
        return False

def test_with_manual_context():
    """
    Alternative test using manually created context string.
    
    This demonstrates how to use the LLM module with pre-built context
    instead of chunk data.
    """
    logger.info("Testing with manually created context...")
    
    try:
        from llm import ContextBuilder, PromptTemplate, OllamaClient
        
        # Create components manually
        context_builder = ContextBuilder()
        prompt_template = PromptTemplate()
        llm_client = OllamaClient()
        
        # Create context manually
        context = create_mock_diabetes_context()
        question = "What are the main treatment options for Type 2 diabetes?"
        
        # Build prompt
        prompt = prompt_template.build_prompt(context, question)
        
        # Generate response
        logger.info("Sending manually built prompt to LLM...")
        start_time = time.time()
        
        answer = llm_client.generate(prompt)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n{'='*50}")
        print("MANUAL CONTEXT TEST")
        print(f"{'='*50}")
        print("QUESTION:")
        print(question)
        print(f"\n{'='*50}")
        print("GENERATED ANSWER:")
        print(answer)
        print(f"\n{'='*50}")
        print(f"Response time: {response_time:.2f} seconds")
        print(f"{'='*50}\n")
        
        logger.info(f"Manual context test completed in {response_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Error in manual context test: {e}")

if __name__ == "__main__":
    """
    Main execution point for the test script.
    
    Usage:
        python tests/test_llm_module.py
    
    This script tests the LLM module independently before integration
    with the retriever module.
    """
    print("LLM Module Test Script")
    print("=" * 50)
    print("Testing RAG LLM module with mock diabetes data...")
    print()
    
    # Run main test
    success = test_llm_module()
    
    if success:
        print("\n" + "=" * 50)
        print("Optional: Run manual context test? (y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice == 'y':
                test_with_manual_context()
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
    
    print("\n" + "=" * 50)
    if success:
        print("✅ LLM module test completed successfully!")
        print("The module is ready for integration with the retriever.")
    else:
        print("❌ LLM module test failed!")
        print("Please check the error messages above and fix issues before proceeding.")
    print("=" * 50)
