"""Authentication module for RegGenome API."""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


class JWTTokenManager:
    """Manages JWT tokens for RegGenome API authentication."""
    
    def __init__(self, token_file_path: str = "key.txt"):
        """Initialize with path to token file."""
        self.token_file_path = Path(token_file_path)
        self._tokens: Optional[Dict[str, Any]] = None
        self._load_tokens()
    
    def _load_tokens(self) -> None:
        """Load tokens from the key file."""
        try:
            if not self.token_file_path.exists():
                logger.warning(f"Token file not found: {self.token_file_path}")
                return
            
            with open(self.token_file_path, 'r') as f:
                token_data = f.read().strip()
            
            # Parse the token data which appears to be in a specific format
            # The format seems to be: JWT_TOKEN,"ExpiresIn":number,"IdToken":"JWT_TOKEN","RefreshToken":"JWT_TOKEN"
            
            # Extract the access token (first JWT)
            access_token_match = re.match(r'^([^"]+)', token_data)
            if not access_token_match:
                logger.error("Could not extract access token")
                return
            
            access_token = access_token_match.group(1)
            
            # Extract ExpiresIn
            expires_in_match = re.search(r'"ExpiresIn":(\d+)', token_data)
            expires_in = int(expires_in_match.group(1)) if expires_in_match else 86400
            
            # Extract IdToken
            id_token_match = re.search(r'"IdToken":"([^"]+)"', token_data)
            id_token = id_token_match.group(1) if id_token_match else ""
            
            # Extract RefreshToken
            refresh_token_match = re.search(r'"RefreshToken":"([^"]+)"', token_data)
            refresh_token = refresh_token_match.group(1) if refresh_token_match else ""
            
            self._tokens = {
                "AccessToken": access_token,
                "ExpiresIn": expires_in,
                "IdToken": id_token,
                "RefreshToken": refresh_token
            }
            
            logger.info("Successfully loaded authentication tokens")
            logger.info(f"Access token expires in {expires_in} seconds")
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            self._tokens = None
    
    def get_access_token(self) -> Optional[str]:
        """Get the current access token."""
        if not self._tokens:
            return None
        return self._tokens.get("AccessToken")
    
    def get_id_token(self) -> Optional[str]:
        """Get the current ID token."""
        if not self._tokens:
            return None
        return self._tokens.get("IdToken")
    
    def get_refresh_token(self) -> Optional[str]:
        """Get the current refresh token."""
        if not self._tokens:
            return None
        return self._tokens.get("RefreshToken")
    
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self._tokens:
            return True
        
        access_token = self.get_access_token()
        if not access_token:
            return True
        
        try:
            # Decode JWT payload to check expiration
            parts = access_token.split('.')
            if len(parts) < 2:
                return True
            
            # Add padding if needed
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            # Decode base64
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)
            
            # Check expiration
            exp_timestamp = payload_data.get('exp')
            if exp_timestamp:
                exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                now = datetime.now(tz=timezone.utc)
                return now >= exp_time
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not decode token expiration: {e}")
            return False
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get information about the current tokens."""
        if not self._tokens:
            return {"status": "no_tokens"}
        
        access_token = self.get_access_token()
        if not access_token:
            return {"status": "no_access_token"}
        
        try:
            # Decode JWT payload
            parts = access_token.split('.')
            if len(parts) < 2:
                return {"status": "invalid_token"}
            
            # Add padding if needed
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            # Decode base64
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)
            
            # Extract useful information
            info = {
                "status": "valid",
                "username": payload_data.get('username'),
                "email": payload_data.get('email'),
                "exp": payload_data.get('exp'),
                "iat": payload_data.get('iat'),
                "scope": payload_data.get('scope'),
                "is_expired": self.is_token_expired()
            }
            
            # Add human-readable expiration time
            if payload_data.get('exp'):
                exp_time = datetime.fromtimestamp(payload_data['exp'], tz=timezone.utc)
                info['expires_at'] = exp_time.isoformat()
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing token info: {e}")
            return {"status": "error", "error": str(e)}
    
    def reload_tokens(self) -> bool:
        """Reload tokens from file."""
        try:
            self._load_tokens()
            return self._tokens is not None
        except Exception as e:
            logger.error(f"Failed to reload tokens: {e}")
            return False


# Global token manager instance
token_manager = JWTTokenManager() 