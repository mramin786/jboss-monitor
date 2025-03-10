#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import threading
import time

# Get the absolute path of the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Configuration - use absolute paths
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'jboss-monitor-backend')
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'jboss-monitor-frontend')

class ApplicationManager:
    def __init__(self):
        self.processes = []
        self.stop_event = threading.Event()

    def start_backend(self):
        """Start the backend Flask server"""
        os.chdir(BACKEND_DIR)
        backend_env = os.environ.copy()
        backend_env['FLASK_ENV'] = 'development'
        backend_env['FLASK_DEBUG'] = '1'
        
        try:
            backend_process = subprocess.Popen(
                [sys.executable, '-m', 'flask', 'run', '--host=0.0.0.0', '--port=5000'],
                env=backend_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.processes.append(backend_process)
            print("\n🔵 Backend server started on http://localhost:5000")
            
            # Stream backend logs
            for line in backend_process.stdout:
                print(f"[BACKEND] {line.strip()}")
        except Exception as e:
            print(f"Failed to start backend: {e}")

    def start_frontend(self):
        """Start the React frontend development server"""
        os.chdir(FRONTEND_DIR)
        
        try:
            frontend_process = subprocess.Popen(
                ['npm', 'start'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.processes.append(frontend_process)
            print("\n🟢 Frontend server started on http://localhost:3000")
            
            # Stream frontend logs
            for line in frontend_process.stdout:
                print(f"[FRONTEND] {line.strip()}")
        except Exception as e:
            print(f"Failed to start frontend: {e}")
            print(f"Current directory: {os.getcwd()}")
            print(f"Frontend directory: {FRONTEND_DIR}")
            print(f"Directory contents: {os.listdir()}")

    def start(self):
        """Start both backend and frontend"""
        # Verify directories exist
        if not os.path.exists(BACKEND_DIR):
            print(f"❌ Backend directory not found: {BACKEND_DIR}")
            return
        
        if not os.path.exists(FRONTEND_DIR):
            print(f"❌ Frontend directory not found: {FRONTEND_DIR}")
            return

        # Start backend and frontend threads
        backend_thread = threading.Thread(target=self.start_backend)
        frontend_thread = threading.Thread(target=self.start_frontend)
        
        backend_thread.start()
        frontend_thread.start()
        
        # Wait for interrupt
        self.wait_for_interrupt()

    def wait_for_interrupt(self):
        """Wait for keyboard interrupt and handle graceful shutdown"""
        try:
            # Wait for keyboard interrupt
            signal.pause()
        except (KeyboardInterrupt, SystemExit):
            self.shutdown()

    def shutdown(self):
        """Gracefully terminate all processes"""
        print("\n🛑 Shutting down...")
        
        # Terminate all processes
        for process in self.processes:
            try:
                process.terminate()
            except Exception as e:
                print(f"Error terminating process: {e}")
        
        # Wait a moment for processes to terminate
        time.sleep(1)
        
        # Force kill if still running
        for process in self.processes:
            try:
                process.kill()
            except Exception as e:
                print(f"Error killing process: {e}")
        
        print("✅ Application shutdown complete.")
        sys.exit(0)

def main():
    # Check dependencies before starting
    def check_dependency(name, check_cmd):
        try:
            subprocess.run(check_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            print(f"❌ {name} is not installed. Please install it first.")
            return False

    dependencies = [
        ("Python", [sys.executable, "-V"]),
        ("Node.js", ["node", "-v"]),
        ("npm", ["npm", "-v"]),
        ("Flask", [sys.executable, "-m", "flask", "--version"])
    ]

    # Check all dependencies
    if all(check_dependency(name, " ".join(map(str, cmd))) for name, cmd in dependencies):
        # Start the application
        app_manager = ApplicationManager()
        app_manager.start()

if __name__ == "__main__":
    main()
