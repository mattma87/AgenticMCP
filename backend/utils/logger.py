"""Audit logging service."""

import json
from typing import Optional, Any
from datetime import datetime
from backend.database.connection import execute


class AuditLogger:
    """Audit logging service."""

    async def log(
        self,
        user_id: int,
        role: str,
        action: str,
        endpoint: Optional[str] = None,
        params: Optional[dict] = None,
        target_id: Optional[int] = None,
        result_count: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        """Log an audit event."""
        # Serialize params to JSON for database storage
        params_json = json.dumps(params) if params else None
        await execute(
            """INSERT INTO audit_logs
            (user_id, role, action, endpoint, params, target_id, result_count, status, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            user_id, role, action, endpoint, params_json, target_id, result_count, status, error_message
        )

    async def log_access(
        self,
        user_id: int,
        role: str,
        endpoint: str,
        params: Optional[dict] = None,
        result_count: Optional[int] = None,
    ):
        """Log API access."""
        await self.log(
            user_id=user_id,
            role=role,
            action="api_call",
            endpoint=endpoint,
            params=params,
            result_count=result_count,
            status="success",
        )

    async def log_error(
        self,
        user_id: int,
        role: str,
        action: str,
        error_message: str,
        endpoint: Optional[str] = None,
    ):
        """Log an error."""
        await self.log(
            user_id=user_id,
            role=role,
            action=action,
            endpoint=endpoint,
            status="error",
            error_message=error_message,
        )


# Global instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
