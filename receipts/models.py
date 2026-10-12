from django.db import models
from django.conf import settings


class Receipt(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "На проверке"
        APPROVED = "approved", "Принят"
        REJECTED = "rejected", "Отклонен"
    

    fn = models.CharField(max_length=32)
    fd = models.CharField(max_length=32)
    fp = models.CharField(max_length=64)

    purchase_datetime = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)


    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    rejection_reason = models.TextField(blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="receipts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fn", "fd", "fp"],
                name="unique_receipt_identifiers",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Чек #{self.pk} — {self.get_status_display()}"