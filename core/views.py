from apps.celebs.models import Celeb, Category, Country
from django.shortcuts import render
from django.db.models import Count, Avg, F, Q

SORT_OPTIONS = {
    'name_asc':   ('name',),
    'name_desc':  ('-name',),
    'followers':  (F('follower_count').desc(nulls_last=True),),
    'rating':     (F('avg_rating').desc(nulls_last=True),),
}
DEFAULT_ORDER = ('type__family__category__name', 'type__family__name', 'type__name', 'name')

def home(request):
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
    filters = Celeb.objects.filter(published=True)
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
        'total_celebs': Celeb.objects.filter(published=True).count(),
        'celebs_count': filters.count(),
        'is_filtered': is_filtered,
        'country_count': Celeb.objects.filter(published=True).values('nationality').distinct().exclude(nationality=None).count(),
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