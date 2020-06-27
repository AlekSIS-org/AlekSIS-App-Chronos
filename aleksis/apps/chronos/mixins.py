from django.db import models
from django.utils.translation import gettext as _

from aleksis.core.managers import CurrentSiteManagerWithoutMigrations
from aleksis.core.mixins import ExtensibleModel

from .managers import ValidityRangeRelatedQuerySet


class ValidityRangeRelatedExtensibleModel(ExtensibleModel):
    """Add relation to validity range."""

    objects = CurrentSiteManagerWithoutMigrations.from_queryset(
        ValidityRangeRelatedQuerySet
    )()

    validity = models.ForeignKey(
        "chronos.ValidityRange",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Linked validity range"),
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
