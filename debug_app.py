import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API keys are set
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

with open("debug_output.txt", "w") as f:
    f.write(f"NEWS_API_KEY is {'set' if NEWS_API_KEY else 'NOT SET'}\n")
    f.write(f"ANTHROPIC_API_KEY is {'set' if ANTHROPIC_API_KEY else 'NOT SET'}\n")
    
    # Try to import the app
    try:
        f.write("Attempting to import app...\n")
        from app import app
        f.write("Successfully imported app\n")
        
        # Try to run the app
        try:
            f.write("Attempting to run app...\n")
            app.run(host='0.0.0.0', port=5008, debug=True)
            f.write("App running successfully\n")
        except Exception as e:
            f.write(f"Error running app: {str(e)}\n")
            f.write(f"Error type: {type(e).__name__}\n")
            import traceback
            f.write(f"Traceback: {traceback.format_exc()}\n")
    except Exception as e:
        f.write(f"Error importing app: {str(e)}\n")
        f.write(f"Error type: {type(e).__name__}\n")
        import traceback
        f.write(f"Traceback: {traceback.format_exc()}\n")
