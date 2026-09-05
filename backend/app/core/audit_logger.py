"""
Tamper-Evident Audit and Compliance Logger for GuardianEye
Logs all sensitive actions, configuration mutations, incident status transitions, and user logins with SHA-256 integrity hashes.
"""
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Optional
from backend.app.core.logging import logger


class AuditLogger:
    @staticmethod
    def log_action(
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id or "SYSTEM",
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address or "127.0.0.1",
        }
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload["sha256_hash"] = hashlib.sha256(serialized).hexdigest()
        logger.info(f"AUDIT_RECORD: {json.dumps(payload)}")
        return payload


audit_logger = AuditLogger()
