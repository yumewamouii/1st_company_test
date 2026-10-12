import re
from datetime import datetime, time
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django import forms
from django.conf import settings
from django.utils.dateparse import parse_date

from .models import Receipt

DIGITS_RE = re.compile(r'^\d+$')
MOSCOW = ZoneInfo('Europe/Moscow')

DUPLICATE_MESSAGE = (
    'Этот чек уже был зарегистрирован. '
    'Повторная отправка с теми же ФН, ФД и ФП невозможна.'
)


class ReceiptSubmitForm(forms.Form):
    fn = forms.CharField(label='ФН', max_length=32)
    fd = forms.CharField(label='Номер чека', max_length=32)
    fp = forms.CharField(label='ФП', max_length=64)
    purchase_date = forms.CharField(label='Дата покупки')
    amount = forms.CharField(label='Сумма')

    def _clean_digits(self, field, min_len, max_len):
        value = (self.cleaned_data.get(field) or '').strip()
        if not value:
            raise forms.ValidationError('Это поле обязательно.')
        if not DIGITS_RE.fullmatch(value):
            raise forms.ValidationError('Допустимы только цифры.')
        if not min_len <= len(value) <= max_len:
            raise forms.ValidationError(
                f'Введите от {min_len} до {max_len} цифр.'
            )
        return value

    def clean_fn(self):
        return self._clean_digits('fn', 1, 32)

    def clean_fd(self):
        return self._clean_digits('fd', 1, 32)

    def clean_fp(self):
        return self._clean_digits('fp', 1, 64)

    def clean_purchase_date(self):
        raw = (self.cleaned_data.get('purchase_date') or '').strip()
        if not raw:
            raise forms.ValidationError('Укажите дату покупки.')

        parsed = None
        for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
            try:
                parsed = datetime.strptime(raw, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            parsed = parse_date(raw)
        if parsed is None:
            raise forms.ValidationError('Введите дату в формате ДД.ММ.ГГГГ.')

        start = settings.PROMOTION_START_DATE
        end = settings.PROMOTION_END_DATE
        if parsed < start or parsed > end:
            raise forms.ValidationError(
                'Дата покупки должна входить в период акции: '
                f'с {start.strftime("%d.%m.%Y")} по {end.strftime("%d.%m.%Y")}.'
            )
        return parsed

    def clean_amount(self):
        raw = (self.cleaned_data.get('amount') or '').strip()
        raw = raw.replace('₽', '').replace(' ', '').replace(',', '.')
        if not raw:
            raise forms.ValidationError('Укажите сумму чека.')
        try:
            amount = Decimal(raw)
        except InvalidOperation:
            raise forms.ValidationError('Введите сумму числом, например 1500.00.')
        if amount < settings.MIN_RECEIPT_AMOUNT:
            min_value = f'{settings.MIN_RECEIPT_AMOUNT:,.0f}'.replace(',', ' ')
            raise forms.ValidationError(
                f'Минимальная стоимость чека должна составлять {min_value} ₽.'
            )
        return amount.quantize(Decimal('0.01'))

    def clean(self):
        cleaned = super().clean()
        fn = cleaned.get('fn')
        fd = cleaned.get('fd')
        fp = cleaned.get('fp')
        if fn and fd and fp:
            exists = Receipt.objects.filter(fn=fn, fd=fd, fp=fp).exists()
            if exists:
                raise forms.ValidationError(DUPLICATE_MESSAGE)
        return cleaned

    def save(self, user):
        purchase_date = self.cleaned_data['purchase_date']
        purchase_datetime = datetime.combine(
            purchase_date,
            time(12, 0),
            tzinfo=MOSCOW,
        )
        return Receipt.objects.create(
            user=user,
            fn=self.cleaned_data['fn'],
            fd=self.cleaned_data['fd'],
            fp=self.cleaned_data['fp'],
            purchase_datetime=purchase_datetime,
            amount=self.cleaned_data['amount'],
            status=Receipt.Status.PENDING,
        )
