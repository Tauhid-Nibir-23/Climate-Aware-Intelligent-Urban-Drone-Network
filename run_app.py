"""
Convenience launcher for Dumki Drone Simulation.
Allows running the Streamlit app by clicking the VS Code Run/Play button.
"""
import sys
import subprocess

if __name__ == "__main__":
    print("Launching Dumki Drone Network Simulation in browser...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

