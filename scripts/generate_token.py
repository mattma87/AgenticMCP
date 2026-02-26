#!/usr/bin/env python3
"""Token generation CLI for AgenticMCP."""

import argparse
import sys
import os
from datetime import timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.auth.jwt import get_jwt_manager


def main():
    # Set debug mode to allow default secret
    os.environ["BACKEND_DEBUG"] = "true"

    parser = argparse.ArgumentParser(description="Generate JWT tokens for AgenticMCP")
    parser.add_argument("--user-id", type=int, default=1, help="User ID (default: 1)")
    parser.add_argument("--role", type=str, default="reader",
                       choices=["admin", "reader", "writer", "support"],
                       help="User role (default: reader)")
    parser.add_argument("--tenant-id", type=int, default=1, help="Tenant ID (default: 1)")
    parser.add_argument("--expires-hours", type=int, default=24,
                       help="Token expiration in hours (default: 24)")
    parser.add_argument("--show-url", action="store_true",
                       help="Show example curl command")

    args = parser.parse_args()

    # Create token
    jwt_manager = get_jwt_manager()
    token = jwt_manager.create_token(
        user_id=args.user_id,
        role=args.role,
        tenant_id=args.tenant_id,
        expires_delta=timedelta(hours=args.expires_hours)
    )

    # Output
    print("=" * 60)
    print("JWT Token Generated")
    print("=" * 60)
    print(f"User ID:    {args.user_id}")
    print(f"Role:       {args.role}")
    print(f"Tenant ID:  {args.tenant_id}")
    print(f"Expires:    {args.expires_hours} hours")
    print()
    print("Token:")
    print("-" * 60)
    print(token)
    print("-" * 60)
    print()

    # Environment variable export
    print("Environment variable:")
    print(f"set MCP_JWT_TOKEN={token}")
    print()

    # Example curl command
    if args.show_url:
        base_url = os.getenv("MCP_API_URL", "http://localhost:8000")
        print("Example API call:")
        print(f"curl -H \"Authorization: Bearer {token}\" \\")
        print(f"     {base_url}/api/v1/users")
        print()

    print("Done!")


if __name__ == "__main__":
    main()
