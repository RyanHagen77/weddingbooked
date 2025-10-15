# reports/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date, timedelta
from contracts.models import Contract, Location
from services.models import Package, ServiceType  # adjust app paths if different
from reports.reports_helpers import DATE_RANGE_DISPLAY, get_date_range  # keep using your helper where it applies

# Extend in-place without changing your helpers:
DATE_RANGE_DISPLAY_SERVICES = {
    **DATE_RANGE_DISPLAY,  # keeps your existing presets (this_month, last_month, custom, etc.)
    'next_week': 'Next Week',
    'next_two_weeks': 'Next Two Weeks',
}

def _future_date_range(preset: str):
    """Compute simple future presets not covered by get_date_range."""
    today = date.today()
    if preset == 'next_week':
        # next Monday .. next Sunday
        days_until_monday = (7 - today.weekday()) % 7 or 7
        start = today + timedelta(days=days_until_monday)
        end = start + timedelta(days=6)
        return start, end
    if preset == 'next_two_weeks':
        # today .. +13 days
        return today, today + timedelta(days=13)
    return None, None

@login_required
def services_report(request):
    # --- inputs ---
    date_range = request.GET.get('date_range') or 'next_two_weeks'  # default to the near future
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    location_id = request.GET.get('location', 'all')
    group_by = request.GET.get('group_by', 'daily')  # 'daily' or 'weekly'
    service_type_id = request.GET.get('service_type', 'all')
    package_id = request.GET.get('package', 'all')

    # --- determine start/end (prefer your helper; add our future presets) ---
    start_date, end_date = None, None
    if date_range in ('next_week', 'next_two_weeks'):
        start_date, end_date = _future_date_range(date_range)
    else:
        start_date, end_date = get_date_range(date_range, start_date_str, end_date_str)

    # handle custom errors the same way as appointments report
    if date_range == 'custom' and (not start_date or not end_date):
        return render(request, 'reports/error.html', {
            'message': 'Please provide both start and end dates for the custom date range.'
        })

    # --- base queryset: contracts with at least one service, on event_date ---
    qs = (Contract.objects
          .filter(event_date__range=(start_date, end_date))
          .filter(
              Q(photography_package__isnull=False) |
              Q(videography_package__isnull=False) |
              Q(dj_package__isnull=False) |
              Q(photobooth_package__isnull=False)
          )
          .select_related(
              'location',
              'photography_package__service_type',
              'videography_package__service_type',
              'dj_package__service_type',
              'photobooth_package__service_type'
          )
          .order_by('event_date', 'contract_id'))

    if location_id != 'all':
        qs = qs.filter(location_id=location_id)

    # Filter by service type / package (applies to any matching column)
    if service_type_id != 'all':
        qs = qs.filter(
            Q(photography_package__service_type_id=service_type_id) |
            Q(videography_package__service_type_id=service_type_id) |
            Q(dj_package__service_type_id=service_type_id) |
            Q(photobooth_package__service_type_id=service_type_id)
        )

    if package_id != 'all':
        qs = qs.filter(
            Q(photography_package_id=package_id) |
            Q(videography_package_id=package_id) |
            Q(dj_package_id=package_id) |
            Q(photobooth_package_id=package_id)
        )

    # --- groupers ---
    def week_start(d):
        return d - timedelta(days=d.weekday())

    # --- build rows ---
    # For each period (day or ISO week), aggregate the packages present.
    # We produce friendly cells with package names per service column and a total-services count.
    rows = []

    def contract_summary(c):
        """Helper to summarize contract for template."""
        return {
            'id': c.contract_id,
            'custom_number': getattr(c, 'custom_contract_number', f'#{c.contract_id}'),
            'location': c.location.name if c.location else '',
            'event_date': c.event_date,
            'photo_pkg': c.photography_package.name if c.photography_package else '',
            'video_pkg': c.videography_package.name if c.videography_package else '',
            'dj_pkg': c.dj_package.name if c.dj_package else '',
            'booth_pkg': c.photobooth_package.name if c.photobooth_package else '',
        }

    def agg(col, items):
        pkgs = [getattr(c, col) for c in items if getattr(c, col)]
        names = [p.name for p in pkgs]
        return {
            'count': len(pkgs),
            'names': sorted(set(names))
        }

    if group_by == 'weekly':
        buckets = {}
        for c in qs:
            wk = c.event_date - timedelta(days=c.event_date.weekday())
            buckets.setdefault(wk, []).append(c)

        for wk_start, items in sorted(buckets.items()):
            wk_end = wk_start + timedelta(days=6)
            photo = agg('photography_package', items)
            video = agg('videography_package', items)
            dj = agg('dj_package', items)
            booth = agg('photobooth_package', items)

            rows.append({
                'period_label': f"{wk_start.strftime('%b %d, %Y')} – {wk_end.strftime('%b %d, %Y')}",
                'photo': photo,
                'video': video,
                'dj': dj,
                'booth': booth,
                'total_services': photo['count'] + video['count'] + dj['count'] + booth['count'],
                'contracts': [contract_summary(c) for c in items],
            })

    else:  # daily
        buckets = {}
        for c in qs:
            buckets.setdefault(c.event_date, []).append(c)

        for d, items in sorted(buckets.items()):
            photo = agg('photography_package', items)
            video = agg('videography_package', items)
            dj = agg('dj_package', items)
            booth = agg('photobooth_package', items)
            rows.append({
                'period_label': d.strftime('%a, %b %d, %Y'),
                'photo': photo,
                'video': video,
                'dj': dj,
                'booth': booth,
                'total_services': photo['count'] + video['count'] + dj['count'] + booth['count'],
                'contracts': [contract_summary(c) for c in items],
            })

    # Dropdown data
    locations = Location.objects.all().order_by('name')
    service_types = ServiceType.objects.all().order_by('name')
    packages = Package.objects.filter(is_active=True).order_by('service_type__name', 'name')

    context = {
        'rows': rows,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'locations': locations,
        'selected_location': location_id,
        'group_by': group_by,
        'service_types': service_types,
        'selected_service_type': service_type_id,
        'packages': packages,
        'selected_package': package_id,
        'date_range': date_range,
        'DATE_RANGE_DISPLAY': DATE_RANGE_DISPLAY_SERVICES,
        'heading': 'Services Report',
    }
    return render(request, 'reports/services_report.html', context)
