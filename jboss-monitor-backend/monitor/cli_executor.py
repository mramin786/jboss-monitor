# monitor/cli_executor.py
import subprocess
import tempfile
import os
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class JBossCliExecutor:
    def __init__(self, host, port, username, password, timeout=30):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def execute_command(self, command):
        """Execute a JBoss CLI command and return the result"""
        # Create a temporary file for credentials
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            temp_file.write(f"{self.username}\n{self.password}")
            credentials_file = temp_file.name

        try:
            # Build the CLI command
            cli_command = [
                "jboss-cli.sh",
                "--controller=" + f"{self.host}:{self.port}",
                "--user=" + self.username,
                "--password=" + self.password,
                "--command=" + command
            ]
            
            # Execute the command
            process = subprocess.run(
                cli_command,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Check for errors
            if process.returncode != 0:
                self.logger.error(f"CLI Error: {process.stderr}")
                return {
                    "success": False,
                    "error": process.stderr,
                    "output": process.stdout
                }
            
            # Parse the output
            output = process.stdout.strip()
            
            # Try to parse as JSON if possible
            try:
                if output.startswith("{") or output.startswith("["):
                    result = json.loads(output)
                else:
                    result = output
                
                return {
                    "success": True,
                    "result": result
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "result": output
                }
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {self.timeout} seconds")
            return {
                "success": False,
                "error": f"Command timed out after {self.timeout} seconds"
            }
        except Exception as e:
            self.logger.error(f"Error executing CLI command: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up the temporary file
            if os.path.exists(credentials_file):
                os.unlink(credentials_file)

    def check_server_status(self):
        """Check if the JBoss server is running"""
        return self.execute_command(":read-attribute(name=server-state)")

    def get_datasources(self):
        """Get list of datasources"""
        return self.execute_command("/subsystem=datasources:read-resource(recursive=true)")

    def check_datasource_connection(self, datasource_name):
        """Test connection to a datasource"""
        return self.execute_command(f"/subsystem=datasources/data-source={datasource_name}:test-connection-in-pool")

    def get_deployments(self):
        """Get list of deployed applications"""
        return self.execute_command("/deployment=*:read-resource(recursive=true)")

    def check_deployment_status(self, deployment_name):
        """Check if a deployment is enabled and running"""
        return self.execute_command(f"/deployment={deployment_name}:read-attribute(name=enabled)")
