# monitor/cli_executor.py
import subprocess
import tempfile
import os
import json
import logging
import time
import shlex
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor
from config import Config

# Thread-local storage for CLI command caching
thread_local = threading.local()

class JBossCliExecutor:
    # Class-level connection pool
    _executor_pool = ThreadPoolExecutor(
        max_workers=Config.CLI_CONNECTION_POOL_SIZE,
        thread_name_prefix="cli-executor-"
    )
    
    # Command result cache
    _cache = {}
    _cache_lock = threading.RLock()
    
    def __init__(self, host, port, username, password, timeout=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout or Config.CLI_TIMEOUT
        self.logger = logging.getLogger(__name__)
        
        # Use the specific path for jboss-cli.sh
        self.jboss_cli_path = '/app/jboss/bin/jboss-cli.sh'
        
        # Create a unique identifier for this connection for caching
        self.connection_id = f"{host}:{port}:{username}"
    
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

    def execute_command(self, command, use_cache=True, cache_ttl=60):
        """Execute a JBoss CLI command and return the result with caching support"""
        # Generate a cache key for this command
        cache_key = f"{self.connection_id}:{command}"
        
        # Check cache for non-modifying commands
        if use_cache and command.startswith(":read-") or command.startswith("/subsystem="):
            with self._cache_lock:
                cache_entry = self._cache.get(cache_key)
                if cache_entry:
                    cache_time, cache_result = cache_entry
                    # Check if cache is still valid
                    if time.time() - cache_time < cache_ttl:
                        self.logger.debug(f"Using cached result for: {command}")
                        return cache_result
        
        try:
            # Check if we should use a simulated response for testing/development
            if os.environ.get('JBOSS_SIMULATION_MODE') == 'true':
                result = self._get_simulated_response(command)
                # Cache the result for read-only commands
                if use_cache and (command.startswith(":read-") or command.startswith("/subsystem=")):
                    with self._cache_lock:
                        self._cache[cache_key] = (time.time(), result)
                return result

            # Verify jboss-cli.sh exists
            if not os.path.exists(self.jboss_cli_path):
                self.logger.error(f"JBoss CLI not found at {self.jboss_cli_path}")
                # For development/testing when jboss-cli.sh might not be available
                if os.environ.get('JBOSS_FALLBACK_SIMULATION') == 'true':
                    self.logger.warning("Using fallback simulation mode due to missing CLI executable")
                    result = self._get_simulated_response(command)
                    if use_cache and (command.startswith(":read-") or command.startswith("/subsystem=")):
                        with self._cache_lock:
                            self._cache[cache_key] = (time.time(), result)
                    return result
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
                "--output-json",  # Add this to force JSON output
                f"--command={command}"
            ]
            
            # Log masked command for security
            masked_cli_command = self._mask_sensitive_data(cli_command)
            self.logger.info(f"Executing CLI command: {' '.join(masked_cli_command)}")
            
            # Execute the command with timeout
            start_time = time.time()
            process = subprocess.run(
                cli_command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                # Protect against shell injection
                shell=False
            )
            execution_time = time.time() - start_time
            self.logger.debug(f"CLI command executed in {execution_time:.2f}s")
            
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
                        result = {
                            "success": True,
                            "result": result.get('result')
                        }
                    else:
                        result = {
                            "success": False,
                            "error": result
                        }
                else:
                    # If not JSON but contains "outcome" => "success", try to parse it
                    if ' => "success"' in output or " => 'success'" in output:
                        self.logger.info("Output appears to be in DMR format, treating as success")
                        result = {
                            "success": True,
                            "result": self._parse_dmr_output(output)
                        }
                    else:
                        result = {
                            "success": True,
                            "result": output
                        }
                
                # Cache the result for read-only commands
                if use_cache and (command.startswith(":read-") or command.startswith("/subsystem=")):
                    with self._cache_lock:
                        self._cache[cache_key] = (time.time(), result)
                
                return result
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse JSON from output: {output}")
                # Try to parse non-JSON CLI output
                if ' => "success"' in output or " => 'success'" in output:
                    self.logger.info("Output appears to be in DMR format, treating as success")
                    result = {
                        "success": True,
                        "result": self._parse_dmr_output(output)
                    }
                else:
                    result = {
                        "success": True,
                        "result": output
                    }
                
                # Cache the result for read-only commands
                if use_cache and (command.startswith(":read-") or command.startswith("/subsystem=")):
                    with self._cache_lock:
                        self._cache[cache_key] = (time.time(), result)
                
                return result
        
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
                
                # Extract data between {}
                import re
                blocks = re.findall(r'{(.*?)}', output, re.DOTALL)
                
                # Extract and parse deployments - supporting all deployment types
                deployments = {}
                for block in blocks:
                    # Look for name
                    name_match = re.search(r'"?name"?\s+=>\s+"([^"]+)"', block)
                    if name_match:
                        deployment_name = name_match.group(1)
                        
                        # Look for enabled status
                        enabled_match = re.search(r'"?enabled"?\s+=>\s+(true|false)', block)
                        enabled = enabled_match and enabled_match.group(1) == 'true'
                        
                        # Add to deployments dict
                        deployments[deployment_name] = {
                            'enabled': enabled
                        }
                
                # Set result
                if deployments:
                    result = deployments
                    
                return result
            
            # For datasources
            if "datasource" in output or "data-source" in output:
                result = {"data-source": {}, "xa-data-source": {}}
                
                # Try to extract datasource names and properties
                import re
                ds_blocks = re.findall(r'"([^"]+)"\s+=>\s+{(.*?)}', output, re.DOTALL)
                
                for ds_name, block in ds_blocks:
                    if "jndi-name" in block:  # This is likely a datasource
                        # Determine datasource type
                        ds_type = "xa-data-source" if "xa-datasource-class" in block else "data-source"
                        
                        # Extract enabled status
                        enabled_match = re.search(r'"?enabled"?\s+=>\s+(true|false)', block)
                        enabled = enabled_match and enabled_match.group(1) == 'true'
                        
                        # Extract connection URL if present
                        conn_url_match = re.search(r'"?connection-url"?\s+=>\s+"([^"]+)"', block)
                        conn_url = conn_url_match.group(1) if conn_url_match else None
                        
                        # Add to result
                        result[ds_type][ds_name] = {
                            "enabled": enabled
                        }
                        if conn_url:
                            result[ds_type][ds_name]["connection-url"] = conn_url
                
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
                    "api.ear": {
                        "enabled": True,
                        "runtime-name": "api.ear"
                    },
                    "utility.jar": {
                        "enabled": True,
                        "runtime-name": "utility.jar"
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
        """Get list of deployed applications (supporting all types, not just .war)"""
        return self.execute_command("/deployment=*:read-resource(recursive=true)")

    def check_deployment_status(self, deployment_name):
        """Check if a deployment is enabled and running"""
        return self.execute_command(f"/deployment={deployment_name}:read-attribute(name=enabled)")

    @classmethod
    def clear_cache(cls):
        """Clear the command cache"""
        with cls._cache_lock:
            cls._cache.clear()

    @classmethod
    def shutdown(cls):
        """Shutdown the executor pool"""
        cls._executor_pool.shutdown(wait=True)
