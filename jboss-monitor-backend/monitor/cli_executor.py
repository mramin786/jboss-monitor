# monitor/cli_executor.py
import subprocess
import tempfile
import os
import json
import logging
import time
import shlex
import traceback

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
            # Check if we should use a simulated response for testing/development
            if os.environ.get('JBOSS_SIMULATION_MODE') == 'true':
                return self._get_simulated_response(command)

            # Verify jboss-cli.sh exists
            if not os.path.exists(self.jboss_cli_path):
                self.logger.error(f"JBoss CLI not found at {self.jboss_cli_path}")
                # For development/testing when jboss-cli.sh might not be available
                if os.environ.get('JBOSS_FALLBACK_SIMULATION') == 'true':
                    self.logger.warning("Using fallback simulation mode due to missing CLI executable")
                    return self._get_simulated_response(command)
                return {
                    "success": False,
                    "error": f"JBoss CLI not found at {self.jboss_cli_path}"
                }

            # Build the CLI command with exact syntax
            cli_command = [
                self.jboss_cli_path,  # Fixed from self.jboss_cli.path to self.jboss_cli_path
                "--connect",
                f"--controller={self.host}:{self.port}",
                f"--user={self.username}",
                f"--password={self.password}",
                "--output-json",  # Add this to force JSON output
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
            self.logger.debug(f"Raw CLI output: {output}")
            
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
                    # If not JSON but contains "outcome" => "success", try to parse it
                    if ' => "success"' in output or " => 'success'" in output:
                        self.logger.info("Output appears to be in DMR format, treating as success")
                        return {
                            "success": True,
                            "result": self._parse_dmr_output(output)
                        }
                    return {
                        "success": True,
                        "result": output
                    }
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse JSON from output: {output}")
                # Try to parse non-JSON CLI output
                if ' => "success"' in output or " => 'success'" in output:
                    self.logger.info("Output appears to be in DMR format, treating as success")
                    return {
                        "success": True,
                        "result": self._parse_dmr_output(output)
                    }
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
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_dmr_output(self, output):
        """
        Parse JBoss DMR format output (with => notation)
        This is a best-effort parser for the common cases we need
        """
        try:
            # Basic parsing for deployment data
            if "deployment" in output and "enabled" in output:
                result = {}
                # Look for deployment names and enabled status
                deployments = []
                
                # Extract data between {}
                import re
                blocks = re.findall(r'{(.*?)}', output, re.DOTALL)
                
                for block in blocks:
                    deployment = {}
                    
                    # Look for name
                    name_match = re.search(r'"?name"?\s+=>\s+"([^"]+)"', block)
                    if name_match:
                        deployment['name'] = name_match.group(1)
                    
                    # Look for enabled status
                    enabled_match = re.search(r'"?enabled"?\s+=>\s+(true|false)', block)
                    if enabled_match:
                        deployment['enabled'] = enabled_match.group(1) == 'true'
                    
                    if deployment:
                        deployments.append(deployment)
                
                if deployments:
                    result['deployments'] = deployments
                    
                return result
            
            # For datasources
            if "datasource" in output or "data-source" in output:
                result = {"data-source": {}}
                
                # Try to extract datasource names and properties
                import re
                ds_blocks = re.findall(r'"([^"]+)"\s+=>\s+{(.*?)}', output, re.DOTALL)
                
                for ds_name, block in ds_blocks:
                    if "jndi-name" in block:  # This is likely a datasource
                        # Extract enabled status
                        enabled_match = re.search(r'"?enabled"?\s+=>\s+(true|false)', block)
                        enabled = enabled_match and enabled_match.group(1) == 'true'
                        
                        result["data-source"][ds_name] = {"enabled": enabled}
                
                return result
            
            # Default - return the raw output
            return output
        except Exception as e:
            self.logger.error(f"Error parsing DMR output: {str(e)}")
            self.logger.error(traceback.format_exc())
            return output

    def _get_simulated_response(self, command):
        """
        Return simulated responses for development/testing without JBoss server
        """
        self.logger.info(f"Using simulated response for command: {command}")
        
        if ":read-attribute(name=server-state)" in command:
            return {
                "success": True,
                "result": "running"
            }
        elif "/subsystem=datasources:read-resource" in command:
            return {
                "success": True,
                "result": {
                    "data-source": {
                        "ExampleDS": {
                            "jndi-name": "java:jboss/datasources/ExampleDS",
                            "enabled": True,
                            "connection-url": "jdbc:h2:mem:test;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE"
                        },
                        "TestDS": {
                            "jndi-name": "java:jboss/datasources/TestDS",
                            "enabled": True,
                            "connection-url": "jdbc:postgresql://localhost:5432/testdb"
                        }
                    },
                    "xa-data-source": {
                        "XAExampleDS": {
                            "jndi-name": "java:jboss/datasources/XAExampleDS",
                            "enabled": True
                        }
                    }
                }
            }
        elif "/deployment=*:read-resource" in command:
            return {
                "success": True,
                "result": {
                    "example.war": {
                        "enabled": True,
                        "runtime-name": "example.war"
                    },
                    "test-app.war": {
                        "enabled": True,
                        "runtime-name": "test-app.war"
                    },
                    "disabled-app.war": {
                        "enabled": False,
                        "runtime-name": "disabled-app.war"
                    }
                }
            }
        elif "test-connection-in-pool" in command:
            return {
                "success": True,
                "result": True
            }
        else:
            return {
                "success": False,
                "error": "Unknown simulated command"
            }

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
