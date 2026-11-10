import uuid

from django.db import models


class SyncModel(models.Model):
    """Base abstracta: PK UUID (generable offline) + campos para sincronización."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)  # pull incremental
    is_deleted = models.BooleanField(default=False, db_index=True)   # soft delete

    class Meta:
        abstract = True
