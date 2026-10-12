import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Receipt

User = get_user_model()

PROMO_START = date(2026, 6, 1)
PROMO_END = date(2026, 12, 31)


@override_settings(
    PROMOTION_START_DATE=PROMO_START,
    PROMOTION_END_DATE=PROMO_END,
    MIN_RECEIPT_AMOUNT=Decimal('1000'),
)
class ReceiptApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='anna',
            password='pass12345',
            email='anna@example.com',
        )
        self.other = User.objects.create_user(
            username='ivan',
            password='pass12345',
        )
        self.client.login(username='anna', password='pass12345')
        self.url = reverse('create_receipt')

    def payload(self, **overrides):
        data = {
            'fn': '1234567890',
            'fd': '111',
            'fp': '222333',
            'purchase_date': '15.07.2026',
            'amount': '1500.00',
        }
        data.update(overrides)
        return data

    def post_json(self, data):
        return self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_creates_receipt_in_pending_status(self):
        response = self.post_json(self.payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['ok'])
        receipt = Receipt.objects.get(pk=body['id'])
        self.assertEqual(receipt.status, Receipt.Status.PENDING)
        self.assertEqual(receipt.user, self.user)
        self.assertEqual(receipt.amount, Decimal('1500.00'))

    def test_rejects_amount_below_minimum(self):
        response = self.post_json(self.payload(amount='999.99'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('amount', response.json()['errors'])
        self.assertFalse(Receipt.objects.exists())

    def test_rejects_date_outside_promo(self):
        response = self.post_json(self.payload(purchase_date='01.05.2026'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('purchase_date', response.json()['errors'])

    def test_inclusive_promo_boundaries(self):
        start = self.post_json(self.payload(fn='1', purchase_date='01.06.2026'))
        end = self.post_json(self.payload(fn='2', purchase_date='31.12.2026'))
        self.assertEqual(start.status_code, 200)
        self.assertEqual(end.status_code, 200)

    def test_duplicate_receipt_returns_friendly_error(self):
        self.assertEqual(self.post_json(self.payload()).status_code, 200)
        response = self.post_json(self.payload(amount='2000'))
        self.assertEqual(response.status_code, 400)
        errors = response.json()['errors']
        message = ' '.join(errors.get('__all__', []))
        self.assertIn('уже был зарегистрирован', message)
        self.assertEqual(Receipt.objects.count(), 1)

    def test_rejected_receipt_cannot_be_resubmitted(self):
        Receipt.objects.create(
            user=self.other,
            fn='1234567890',
            fd='111',
            fp='222333',
            purchase_datetime='2026-07-15 12:00:00+03:00',
            amount=Decimal('1500.00'),
            status=Receipt.Status.REJECTED,
            rejection_reason='Товар не участвует в акции.',
        )
        response = self.post_json(self.payload())
        self.assertEqual(response.status_code, 400)
        self.assertIn('уже был зарегистрирован', ' '.join(response.json()['errors']['__all__']))

    def test_cabinet_shows_only_own_receipts_newest_first(self):
        first = Receipt.objects.create(
            user=self.user,
            fn='1',
            fd='1',
            fp='1',
            purchase_datetime='2026-07-01 12:00:00+03:00',
            amount=Decimal('1000.00'),
        )
        second = Receipt.objects.create(
            user=self.user,
            fn='2',
            fd='2',
            fp='2',
            purchase_datetime='2026-07-02 12:00:00+03:00',
            amount=Decimal('2000.00'),
        )
        Receipt.objects.create(
            user=self.other,
            fn='3',
            fd='3',
            fp='3',
            purchase_datetime='2026-07-03 12:00:00+03:00',
            amount=Decimal('3000.00'),
        )
        response = self.client.get(reverse('cabinet'))
        self.assertContains(response, '2 000')
        self.assertNotContains(response, '3 000')
        self.assertEqual(list(response.context['page_obj'])[0].pk, second.pk)
        self.assertEqual(list(response.context['page_obj'])[1].pk, first.pk)

    def test_pagination_is_ten_per_page(self):
        for i in range(11):
            Receipt.objects.create(
                user=self.user,
                fn=str(1000 + i),
                fd=str(i),
                fp=str(i),
                purchase_datetime='2026-07-15 12:00:00+03:00',
                amount=Decimal('1000.00'),
            )
        first_page = self.client.get(reverse('cabinet'))
        second_page = self.client.get(reverse('cabinet'), {'page': 2})
        self.assertEqual(len(first_page.context['page_obj']), 10)
        self.assertEqual(len(second_page.context['page_obj']), 1)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('cabinet'))
        self.assertEqual(response.status_code, 302)

    def test_promo_dates_come_from_settings(self):
        response = self.client.get(reverse('register'))
        self.assertContains(response, '01.06.2026')
        self.assertContains(response, '31.12.2026')
