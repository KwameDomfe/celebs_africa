from apps.celebs.models import Celeb, Category, Country
from django.shortcuts import render
from django.db.models import Count, Avg, F

def home(request):
    categories = Category.objects.prefetch_related('families__types').order_by('name')
    countries = Country.objects.all()
    celebs = Celeb.objects.select_related('type__family__category', 'nationality').annotate(
        follower_count=Count('followers'),
        avg_rating=Avg('reviews__rating'),
    ).order_by(
        'type__family__category__name', 'type__family__name', 'type__name', 'name'
    )
    cat_id = request.GET.get('category', '')
    family_id = request.GET.get('family', '')
    type_id = request.GET.get('type', '')
    country_id = request.GET.get('country', '')
    q = request.GET.get('q', '')
    q_filter = q.strip()
    if cat_id:
        celebs = celebs.filter(type__family__category_id=cat_id)
    if family_id:
        celebs = celebs.filter(type__family_id=family_id)
    if type_id:
        celebs = celebs.filter(type_id=type_id)
    if country_id:
        celebs = celebs.filter(nationality_id=country_id)
    if q_filter:
        celebs = celebs.filter(name__icontains=q_filter) | celebs.filter(street_name__icontains=q_filter)
    context = {
        'celebs': celebs,
        'categories': categories,
        'countries': countries,
        'selected_category': cat_id,
        'selected_family': family_id,
        'selected_type': type_id,
        'selected_country': country_id,
        'q': q,
    }
    return render(request, 'home.html', context)


def top_celebs(request):
    cat_id = request.GET.get('category', '')
    family_id = request.GET.get('family', '')
    type_id = request.GET.get('type', '')
    q = request.GET.get('q', '').strip()
    categories = Category.objects.prefetch_related('families__types').order_by('name')
    celebs = (
        Celeb.objects.select_related('type__family__category', 'nationality')
        .annotate(
            follower_count=Count('followers'),
            avg_rating=Avg('reviews__rating'),
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