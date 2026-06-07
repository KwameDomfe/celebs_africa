from apps.celebs.models import Celeb, Category, Country
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Count, Avg, F, Q

SORT_OPTIONS = {
    'name_asc':   ('name',),
    'name_desc':  ('-name',),
    'followers':  (F('follower_count').desc(nulls_last=True),),
    'rating':     (F('avg_rating').desc(nulls_last=True),),
}
DEFAULT_ORDER = ('type__family__category__name', 'type__family__name', 'type__name', 'name')

def home(request):
    published_celebs = Celeb.objects.filter(published=True)
    categories = Category.objects.prefetch_related('families__types').order_by('name')
    countries = Country.objects.all()
    cat_id = request.GET.get('category', '')
    family_id = request.GET.get('family', '')
    type_id = request.GET.get('type', '')
    country_id = request.GET.get('country', '')
    q = request.GET.get('q', '')
    sort = request.GET.get('sort', 'default') or 'default'
    q_filter = q.strip()

    # Base filter queryset (no annotations — for accurate counting)
    filters = published_celebs
    if cat_id:
        filters = filters.filter(type__family__category_id=cat_id)
    if family_id:
        filters = filters.filter(type__family_id=family_id)
    if type_id:
        filters = filters.filter(type_id=type_id)
    if country_id:
        filters = filters.filter(nationality_id=country_id)
    if q_filter:
        filters = filters.filter(Q(name__icontains=q_filter) | Q(street_name__icontains=q_filter))

    # Annotated queryset for display (same filters applied)
    celebs = filters.select_related('type__family__category', 'nationality').annotate(
        follower_count=Count('followers', distinct=True),
        avg_rating=Avg('reviews__rating', distinct=True),
    ).order_by(*SORT_OPTIONS.get(sort, DEFAULT_ORDER))

    visible_limit = 12
    if request.user.is_authenticated:
        visible_celebs = celebs
        locked_profiles_count = 0
    else:
        visible_celebs = celebs[:visible_limit]
        locked_profiles_count = max(filters.count() - visible_limit, 0)

    trending_celebs = (
        published_celebs.select_related('type__family__category', 'nationality')
        .annotate(
            follower_count=Count('followers', distinct=True),
            avg_rating=Avg('reviews__rating', distinct=True),
        )
        .order_by(F('follower_count').desc(nulls_last=True), F('avg_rating').desc(nulls_last=True), 'name')[:10]
    )

    spotlight_categories = (
        Category.objects.annotate(
            celeb_count=Count(
                'families__types__celebs',
                filter=Q(families__types__celebs__published=True) & Q(families__types__celebs__nationality__isnull=False),
                distinct=True,
            )
        )
        .filter(celeb_count__gt=0)
        .order_by('-celeb_count', 'name')[:6]
    )

    category_media_items = []
    for category in spotlight_categories[:4]:
        representative = (
            published_celebs.filter(type__family__category=category, image__isnull=False)
            .exclude(image='')
            .annotate(
                follower_count=Count('followers', distinct=True),
                avg_rating=Avg('reviews__rating', distinct=True),
            )
            .only('name', 'image', 'slug')
            .order_by(F('avg_rating').desc(nulls_last=True), F('follower_count').desc(nulls_last=True), 'name')
            .first()
        )
        category_media_items.append({
            'category': category,
            'celeb': representative,
        })

    selected_country_name = ''
    if country_id:
        selected_country_obj = countries.filter(pk=country_id).first()
        if selected_country_obj:
            selected_country_name = selected_country_obj.name

    # Keep this metric aligned with the active list filters shown on the page.
    geo_profiles_count = (
        filters.count()
        if country_id else
        filters.exclude(nationality=None).count()
    )

    is_filtered = any([cat_id, family_id, type_id, country_id, q_filter])
    context = {
        'celebs': celebs,
        'categories': categories,
        'countries': countries,
        'selected_category': cat_id,
        'selected_family': family_id,
        'selected_type': type_id,
        'selected_country': country_id,
        'selected_sort': sort,
        'q': q,
        'total_celebs': published_celebs.count(),
        'celebs_count': filters.count(),
        'is_filtered': is_filtered,
        'country_count': published_celebs.values('nationality').distinct().exclude(nationality=None).count(),
        'trending_celebs': trending_celebs,
        'spotlight_categories': spotlight_categories,
        'category_media_items': category_media_items,
        'geo_profiles_count': geo_profiles_count,
        'geo_scope_label': selected_country_name or 'Africa',
        'visible_celebs': visible_celebs,
        'locked_profiles_count': locked_profiles_count,
        'is_soft_gated': (not request.user.is_authenticated) and locked_profiles_count > 0,
    }
    return render(request, 'home.html', context)


def top_celebs(request):
    cat_id = request.GET.get('category', '')
    family_id = request.GET.get('family', '')
    type_id = request.GET.get('type', '')
    q = request.GET.get('q', '').strip()
    categories = Category.objects.prefetch_related('families__types').order_by('name')
    celebs = (
        Celeb.objects.filter(published=True).select_related('type__family__category', 'nationality')
        .annotate(
            follower_count=Count('followers', distinct=True),
            avg_rating=Avg('reviews__rating', distinct=True),
        )
        .order_by(F('avg_rating').desc(nulls_last=True), F('follower_count').desc(nulls_last=True))
    )
    if cat_id:
        celebs = celebs.filter(type__family__category_id=cat_id)
    if family_id:
        celebs = celebs.filter(type__family_id=family_id)
    if type_id:
        celebs = celebs.filter(type_id=type_id)
    if q:
        celebs = celebs.filter(name__icontains=q) | celebs.filter(street_name__icontains=q)
    return render(request, 'top_celebs.html', {
        'celebs': celebs,
        'categories': categories,
        'selected_category': cat_id,
        'selected_family': family_id,
        'selected_type': type_id,
        'q': q,
    })


def sitemap_xml(request):
    urls = [
        (request.build_absolute_uri(reverse('home')), '1.0', 'weekly'),
        (request.build_absolute_uri(reverse('top_celebs')), '0.9', 'weekly'),
        (request.build_absolute_uri(reverse('celebs_home')), '0.9', 'weekly'),
    ]

    for celeb in Celeb.objects.filter(published=True).select_related('type__family__category').order_by('name'):
        urls.append((request.build_absolute_uri(celeb.get_absolute_url()), '0.7', 'weekly'))

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority, changefreq in urls:
        xml_lines.extend([
            '  <url>',
            f'    <loc>{url}</loc>',
            f'    <changefreq>{changefreq}</changefreq>',
            f'    <priority>{priority}</priority>',
            '  </url>',
        ])
    xml_lines.append('</urlset>')
    return HttpResponse('\n'.join(xml_lines), content_type='application/xml')