#!/usr/bin/env python3
"""
Helper script to install Pomodoro CLI dependencies
"""
import subprocess
import sys
import platform
import os

def install_dependencies():
    """Install dependencies required by the Pomodoro CLI"""
    
    print("🍅 Pomodoro CLI - Dependency Installer")
    print("--------------------------------------")
    
    # Check if pip is available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("❌ Error: pip is not installed or not working properly.")
        print("Please install pip to continue: https://pip.pypa.io/en/stable/installation/")
        sys.exit(1)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ Error: requirements.txt file not found.")
        print("Please make sure you're running this script from the correct directory.")
        sys.exit(1)
    
    print("Installing dependencies from requirements.txt...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\n✅ Dependencies installed successfully!")
        
        # Special message for macOS users regarding notifications
        if platform.system() == 'Darwin':
            try:
                import pync
                print("\n✅ macOS notifications are enabled! You'll receive notifications when:")
                print("  - Work sessions end")
                print("  - Breaks end")
                print("  - Less than a minute remains in your work session")
            except ImportError:
                print("\n⚠️ The pync package couldn't be imported even though installation was attempted.")
                print("   Desktop notifications might not work.")
                print("   You can try installing it manually: pip install pync")
        
        print("\nYou're all set! Run the timer with:")
        print("python3 pomodoro.py")
        
    except subprocess.CalledProcessError:
        print("\n❌ Error occurred during dependency installation.")
        print("You can try running the installer manually:")
        print("pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    install_dependencies()