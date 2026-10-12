from django.contrib import admin
from .models import Receipt


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fn",
        "fd",
        "fp",
        "amount",
        "purchase_datetime",
        "status",
        "user",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("fn", "fd", "fp", "user__username")
    readonly_fields = ("user", "created_at")
    list_per_page = 20