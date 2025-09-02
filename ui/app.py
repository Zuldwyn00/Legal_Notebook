#!/usr/bin/env python3
"""
Launch script for the AI Knowledge Assistant UI.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path so we can import modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import customtkinter as ctk
    from ui.main_window import MainWindow
    print("✅ All dependencies loaded successfully")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please install required packages:")
    print("pip install customtkinter")
    sys.exit(1)


def main():
    """
    Main entry point for the UI application.
    """
    print("🚀 Starting AI Knowledge Assistant...")
    
    try:
        # Create and run the application
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
