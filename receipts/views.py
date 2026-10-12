import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import DUPLICATE_MESSAGE, ReceiptSubmitForm
from .models import Receipt

PAGE_SIZE = 10


def _pagination_items(page):
    last = page.paginator.num_pages
    current = page.number
    if last <= 7:
        return list(range(1, last + 1))

    items = [1]
    start = max(2, current - 1)
    end = min(last - 1, current + 2)

    if start > 2:
        items.append('…')
    items.extend(range(start, end + 1))
    if end < last - 1:
        items.append('…')
    items.append(last)
    return items


def landing(request):
    return render(request, 'receipts/landing.html')


@login_required
def cabinet(request):
    queryset = Receipt.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(queryset, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))
    return render(
        request,
        'receipts/cabinet.html',
        {
            'page_obj': page,
            'pagination_items': _pagination_items(page) if page.paginator.num_pages else [],
            'receipts_total': paginator.count,
            'active_nav': 'cabinet',
        },
    )


@login_required
@ensure_csrf_cookie
def register(request):
    return render(
        request,
        'receipts/register.html',
        {'active_nav': 'cabinet'},
    )


@login_required
@require_POST
def create_receipt(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse(
            {'ok': False, 'errors': {'__all__': ['Некорректный запрос.']}},
            status=400,
        )

    form = ReceiptSubmitForm(payload)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)

    try:
        receipt = form.save(user=request.user)
    except IntegrityError:
        return JsonResponse(
            {'ok': False, 'errors': {'__all__': [DUPLICATE_MESSAGE]}},
            status=400,
        )

    return JsonResponse({'ok': True, 'id': receipt.pk, 'status': receipt.status})


@login_required
def rules(request):
    return render(request, 'receipts/rules.html', {'active_nav': 'rules'})


@login_required
def profile(request):
    return render(request, 'receipts/profile.html', {'active_nav': 'profile'})
