from django import forms
from django.contrib import admin
from .models import Receipt


from import_export.admin import ExportMixin
from import_export import resources


class ReceiptResource(resources.ModelResource):
    class Meta:
        model = Receipt
        fields = ("id", "fn", "fd", "fp", "amount", "purchase_datetime", "status", "rejection_reason", "user", "created_at")
        export_order = ("id", "fn", "fd", "fp", "amount", "purchase_datetime", "status", "rejection_reason", "user", "created_at")


class ReceiptAdminForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        reason = cleaned_data.get("rejection_reason")

        if status == Receipt.Status.REJECTED and not reason:
            self.add_error(
                "rejection_reason",
                "Укажите причину отказа для отклоненного чека."
            )

        return cleaned_data


@admin.register(Receipt)
class ReceiptAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "fn",
        "fd",
        "fp",
        "amount",
        "purchase_datetime",
        "status",
        "rejection_reason",
        "user",
        "created_at",
    )

    resource_class = ReceiptResource

    list_filter = ("status", "created_at")
    search_fields = ("fn", "fd", "fp", "user__username")
    readonly_fields = ("user", "created_at")
    list_per_page = 20