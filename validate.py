#!/usr/bin/env python3
"""Validation script to check CornerGuide installation."""

import sys
import os
import importlib
from pathlib import Path

def check_imports():
    """Check if all required packages can be imported."""
    
    required_packages = [
        ('langchain', 'LangChain core'),
        ('langchain_openai', 'LangChain OpenAI'),
        ('langchain_core', 'LangChain core components'),
        ('langgraph', 'LangGraph orchestration'),
        ('qdrant_client', 'Qdrant vector database client'),
        ('streamlit', 'Streamlit web framework'),
        ('PyPDF2', 'PDF processing'),
        ('pydantic', 'Data validation'),
        ('dotenv', 'Environment variables'),
        ('openai', 'OpenAI API client'),
    ]
    
    print("🔍 Checking package imports...")
    
    failed_imports = []
    
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - {description}")
        except ImportError as e:
            print(f"❌ {package} - {description}: {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def check_project_structure():
    """Check if project structure is correct."""
    
    print("\n🏗️  Checking project structure...")
    
    required_files = [
        'config.py',
        'requirements.txt',
        'app.py', 
        'run.py',
        '.env.template',
        'src/__init__.py',
        'src/models/rules.py',
        'src/agents/retrieval_agent.py',
        'src/agents/answer_generator.py',
        'src/agents/medical_research_agent.py',
        'src/extraction/pdf_processor.py',
        'src/vector_db/qdrant_setup.py',
        'src/orchestration/workflow.py',
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_environment():
    """Check environment configuration."""
    
    print("\n🌍 Checking environment...")
    
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
        
        # Check for required API keys
        with open(env_file) as f:
            content = f.read()
            
            # Check OpenAI API key
            if 'OPENAI_API_KEY=' in content and 'your_openai_key_here' not in content:
                print("✅ OpenAI API key appears to be set")
            else:
                print("⚠️  OpenAI API key not set in .env file")
                return False
            
            # Check Cohere API key
            if 'COHERE_API_KEY=' in content and 'your_cohere_key_here' not in content:
                print("✅ Cohere API key appears to be set")
            else:
                print("⚠️  Cohere API key not set in .env file (required for reranking)")
                return False
    else:
        print("⚠️  .env file not found")
        return False
    
    return True

def check_assets():
    """Check assets directory."""
    
    print("\n📁 Checking assets directory...")
    
    assets_dir = Path('assets')
    if assets_dir.exists():
        pdf_files = list(assets_dir.glob('*.pdf'))
        if pdf_files:
            print(f"✅ Found {len(pdf_files)} PDF files:")
            for pdf in pdf_files:
                print(f"   - {pdf.name}")
        else:
            print("⚠️  No PDF files found in assets directory")
            return False
    else:
        print("❌ Assets directory not found")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality."""
    
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test config import
        import config
        print("✅ Config module imports successfully")
        
        # Test model imports
        from src.models.rules import RuleChunk
        print("✅ Pydantic models import successfully")
        
        # Test agent imports
        from src.agents.retrieval_agent import RetrievalAgent
        from src.agents.medical_research_agent import MedicalResearchAgent
        print("✅ Agent classes import successfully")
        
        # Test workflow import
        from src.orchestration.workflow import BJJRuleWorkflow
        print("✅ Workflow imports successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Main validation process."""
    
    print("🥋 CornerGuide Validation")
    print("=" * 25)
    
    checks = [
        ("Package imports", check_imports),
        ("Project structure", check_project_structure), 
        ("Environment setup", check_environment),
        ("Assets directory", check_assets),
        ("Basic functionality", test_basic_functionality),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{'='*50}")
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Validation Summary")
    print(f"{'='*50}")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All checks passed! CornerGuide is ready to run.")
        print("Run with: python run.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())