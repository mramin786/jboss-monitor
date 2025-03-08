# monitor/cli_executor.py
import subprocess
import tempfile
import os
import json
import logging
import time
import shlex

class JBossCliExecutor:
    def __init__(self, host, port, username, password, timeout=30):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Use the specific path for jboss-cli.sh
        self.jboss_cli_path = '/app/jboss/bin/jboss-cli.sh'

    def _mask_sensitive_data(self, command_list):
        """
        Create a copy of the command list with sensitive data masked
        Helps in logging without exposing credentials
        """
        masked_command = command_list.copy()
        for i, part in enumerate(masked_command):
            if '--password=' in part:
                masked_command[i] = '--password=****'
        return masked_command

    def execute_command(self, command):
        """Execute a JBoss CLI command and return the result"""
        try:
            # Verify jboss-cli.sh exists
            if not os.path.exists(self.jboss_cli_path):
                self.logger.error(f"JBoss CLI not found at {self.jboss_cli_path}")
                return {
                    "success": False,
                    "error": f"JBoss CLI not found at {self.jboss_cli_path}"
                }

            # Build the CLI command with exact syntax
            cli_command = [
                self.jboss_cli_path,
                "--connect",
                f"--controller={self.host}:{self.port}",
                f"--user={self.username}",
                f"--password={self.password}",
                f"--command={command}"
            ]
            
            # Log masked command for security
            masked_cli_command = self._mask_sensitive_data(cli_command)
            self.logger.info(f"Executing CLI command: {' '.join(masked_cli_command)}")
            
            # Execute the command
            process = subprocess.run(
                cli_command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                # Protect against shell injection
                shell=False
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
                # Specific parsing for JBoss CLI output
                if output.startswith("{"):
                    result = json.loads(output)
                    # Check for JBoss CLI specific outcome
                    if result.get('outcome') == 'success':
                        return {
                            "success": True,
                            "result": result.get('result')
                        }
                    else:
                        return {
                            "success": False,
                            "error": result
                        }
                else:
                    return {
                        "success": True,
                        "result": output
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
        except FileNotFoundError:
            self.logger.error(f"JBoss CLI executable not found: {self.jboss_cli_path}")
            return {
                "success": False,
                "error": f"JBoss CLI executable not found: {self.jboss_cli_path}"
            }
        except Exception as e:
            self.logger.error(f"Error executing CLI command: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    # Rest of the methods remain the same
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
