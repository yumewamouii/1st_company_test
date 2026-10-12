from django.conf import settings


def promo(request):
    return {
        'promo_start': settings.PROMOTION_START_DATE,
        'promo_end': settings.PROMOTION_END_DATE,
        'min_receipt_amount': settings.MIN_RECEIPT_AMOUNT,
    }
