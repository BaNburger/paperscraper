"""Re-encrypt legacy model keys using v2 envelope format.

Revision ID: model_key_encryption_v1
Revises: research_groups_indexes_v1
Create Date: 2026-02-17 21:40:00.000000
"""

from __future__ import annotations

import base64
from typing import Any

import sqlalchemy as sa

from alembic import op
from paper_scraper.core.secrets import decrypt_secret, encrypt_secret

# revision identifiers, used by Alembic.
revision: str = "model_key_encryption_v1"
down_revision: str | None = "research_groups_indexes_v1"
branch_labels: str | None = None
depends_on: str | None = None


def _decode_legacy_base64(value: str) -> str | None:
    """Decode legacy base64 model key payloads."""
    try:
        decoded = base64.b64decode(value.encode("utf-8"), validate=True).decode("utf-8")
    except Exception:
        return None
    return decoded if decoded else None


def _encode_legacy_base64(value: str) -> str:
    """Encode model key payload for downgrade compatibility."""
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")


def upgrade() -> None:
    """Migrate base64 model keys to enc:v1 encrypted envelope format."""
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT id, api_key_encrypted
            FROM model_configurations
            WHERE api_key_encrypted IS NOT NULL
            """
        )
    ).mappings()

    for row in rows:
        row_data = dict(row)
        key_id = row_data.get("id")
        raw_value = row_data.get("api_key_encrypted")

        if key_id is None or not isinstance(raw_value, str) or not raw_value:
            continue

        if raw_value.startswith("enc:v1:"):
            continue

        legacy_plaintext = _decode_legacy_base64(raw_value)
        if legacy_plaintext is None:
            continue

        encrypted_value = f"enc:v1:{encrypt_secret(legacy_plaintext)}"
        connection.execute(
            sa.text(
                """
                UPDATE model_configurations
                SET api_key_encrypted = :value
                WHERE id = :id
                """
            ),
            {"id": key_id, "value": encrypted_value},
        )


def downgrade() -> None:
    """Best-effort rollback to legacy base64 model key format."""
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT id, api_key_encrypted
            FROM model_configurations
            WHERE api_key_encrypted LIKE 'enc:v1:%'
            """
        )
    ).mappings()

    for row in rows:
        row_data: dict[str, Any] = dict(row)
        key_id = row_data.get("id")
        raw_value = row_data.get("api_key_encrypted")
        if key_id is None or not isinstance(raw_value, str):
            continue

        encrypted_payload = raw_value.replace("enc:v1:", "", 1)
        try:
            plaintext = decrypt_secret(encrypted_payload)
        except Exception:
            continue

        connection.execute(
            sa.text(
                """
                UPDATE model_configurations
                SET api_key_encrypted = :value
                WHERE id = :id
                """
            ),
            {"id": key_id, "value": _encode_legacy_base64(plaintext)},
        )
