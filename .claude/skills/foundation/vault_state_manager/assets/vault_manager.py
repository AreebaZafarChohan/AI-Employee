"""
vault_manager.py
Secure vault state management with proper error handling and auditing
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hvac  # HashiCorp Vault client
from dataclasses import dataclass

# Configure logging (never log actual secrets)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Vault configuration from environment"""
    addr: str
    token: str
    namespace: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> 'VaultConfig':
        """Load configuration from environment variables"""
        addr = os.getenv('VAULT_ADDR')
        token = os.getenv('VAULT_TOKEN')

        if not addr or not token:
            raise ValueError("VAULT_ADDR and VAULT_TOKEN must be set")

        return cls(
            addr=addr,
            token=token,
            namespace=os.getenv('VAULT_NAMESPACE'),
            timeout=int(os.getenv('VAULT_OPERATION_TIMEOUT', '30')),
            max_retries=int(os.getenv('VAULT_MAX_RETRIES', '3'))
        )


class VaultStateManager:
    """Secure vault state manager with audit logging"""

    def __init__(self, config: Optional[VaultConfig] = None):
        self.config = config or VaultConfig.from_env()
        self.client = hvac.Client(
            url=self.config.addr,
            token=self.config.token,
            namespace=self.config.namespace
        )

        if not self.client.is_authenticated():
            raise RuntimeError("Vault authentication failed")

        logger.info("Vault client initialized", extra={
            'vault_addr': self.config.addr,
            'namespace': self.config.namespace
        })

    def _audit_log(self, action: str, path: str, status: str, error: Optional[str] = None):
        """Log audit trail for vault operations"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'path': path,
            'status': status,
            'user': os.getenv('USER', 'unknown')
        }

        if error:
            log_entry['error'] = error

        # Write to audit log file or send to logging system
        audit_log_path = os.getenv('VAULT_AUDIT_LOG_PATH')
        if audit_log_path:
            with open(audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        logger.info(f"Vault operation: {action} on {path} - {status}")

    def read_secret(self, path: str, mount_point: str = 'secret') -> Optional[Dict[str, Any]]:
        """
        Read secret from vault

        Args:
            path: Secret path (e.g., 'myapp/config')
            mount_point: Vault mount point (default: 'secret')

        Returns:
            Secret data dictionary or None if not found
        """
        full_path = f"{mount_point}/data/{path}"

        try:
            self._audit_log('READ', full_path, 'ATTEMPT')

            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )

            self._audit_log('READ', full_path, 'SUCCESS')
            return response['data']['data']

        except hvac.exceptions.InvalidPath:
            self._audit_log('READ', full_path, 'NOT_FOUND')
            logger.warning(f"Secret not found at path: {full_path}")
            return None

        except hvac.exceptions.Forbidden:
            self._audit_log('READ', full_path, 'FORBIDDEN')
            logger.error(f"Access denied to path: {full_path}")
            raise

        except Exception as e:
            self._audit_log('READ', full_path, 'ERROR', str(e))
            logger.error(f"Error reading secret: {e}")
            raise

    def write_secret(self, path: str, data: Dict[str, Any], mount_point: str = 'secret') -> bool:
        """
        Write secret to vault

        Args:
            path: Secret path (e.g., 'myapp/config')
            data: Secret data dictionary
            mount_point: Vault mount point (default: 'secret')

        Returns:
            True if successful, False otherwise
        """
        full_path = f"{mount_point}/data/{path}"

        # Validate data
        if not data or not isinstance(data, dict):
            raise ValueError("Data must be a non-empty dictionary")

        try:
            self._audit_log('WRITE', full_path, 'ATTEMPT')

            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=mount_point
            )

            self._audit_log('WRITE', full_path, 'SUCCESS')
            return True

        except hvac.exceptions.Forbidden:
            self._audit_log('WRITE', full_path, 'FORBIDDEN')
            logger.error(f"Access denied to path: {full_path}")
            raise

        except Exception as e:
            self._audit_log('WRITE', full_path, 'ERROR', str(e))
            logger.error(f"Error writing secret: {e}")
            raise

    def update_secret(self, path: str, updates: Dict[str, Any], mount_point: str = 'secret') -> bool:
        """
        Update existing secret (merge with existing data)

        Args:
            path: Secret path
            updates: Dictionary of fields to update
            mount_point: Vault mount point

        Returns:
            True if successful
        """
        # Read existing data
        existing_data = self.read_secret(path, mount_point)

        if existing_data is None:
            logger.warning(f"Secret not found, creating new one at: {path}")
            return self.write_secret(path, updates, mount_point)

        # Merge updates
        merged_data = {**existing_data, **updates}

        return self.write_secret(path, merged_data, mount_point)

    def delete_secret(self, path: str, mount_point: str = 'secret') -> bool:
        """
        Delete secret from vault

        Args:
            path: Secret path
            mount_point: Vault mount point

        Returns:
            True if successful
        """
        full_path = f"{mount_point}/data/{path}"

        try:
            self._audit_log('DELETE', full_path, 'ATTEMPT')

            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=mount_point
            )

            self._audit_log('DELETE', full_path, 'SUCCESS')
            return True

        except Exception as e:
            self._audit_log('DELETE', full_path, 'ERROR', str(e))
            logger.error(f"Error deleting secret: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize manager (loads config from environment)
    manager = VaultStateManager()

    # Read secret
    config = manager.read_secret('myapp/config')
    if config:
        print(f"Retrieved {len(config)} configuration keys")

    # Update secret
    manager.update_secret('myapp/config', {
        'database_url': 'postgresql://...',
        'api_key': 'new-key-value'
    })

    print("Vault operations completed successfully")
