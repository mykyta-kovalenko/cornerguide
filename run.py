import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    required_vars = ["OPENAI_API_KEY", "COHERE_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return False
    
    return True

def run_streamlit():
    if not check_environment():
        sys.exit(1)
    
    print("🥋 Starting CornerGuide - BJJ Rules Assistant...")
    print("📝 The application will initialize by processing PDF documents on first run.")
    print("🌐 Opening browser at http://localhost:8501")
    
    try:
        subprocess.run([
            "streamlit", "run", "app.py",
            "--theme.base", "dark",
            "--theme.primaryColor", "#ff6b35",
            "--theme.backgroundColor", "#0e1117",
            "--theme.secondaryBackgroundColor", "#262730",
            "--theme.textColor", "#fafafa",
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 CornerGuide stopped by user.")

if __name__ == "__main__":
    run_streamlit()