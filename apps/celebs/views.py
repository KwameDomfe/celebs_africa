
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Celeb, Like, Comment, Family, Type, Category, Follow, Review, Country, CelebPhoto, CelebSocialLink


def _save_social_links(request, celeb):
	"""Parse link_platform / link_url POST lists and replace all social links for celeb."""
	platforms = request.POST.getlist('link_platform')
	urls = request.POST.getlist('link_url')
	celeb.social_links.all().delete()
	order = 0
	for platform, url in zip(platforms, urls):
		url = url.strip()
		if platform and url:
			CelebSocialLink.objects.create(celeb=celeb, platform=platform, url=url, order=order)
			order += 1


def staff_required(view_func):
    """Decorator: must be logged in and staff."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden('You do not have permission to perform this action.')
        return view_func(request, *args, **kwargs)
    return wrapper


def celebs_home(request):
	categories = Category.objects.prefetch_related('families__types').order_by('name')
	countries = Country.objects.all()
	celebs = Celeb.objects.filter(published=True).select_related('type__family__category').annotate(
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
	return render(request, 'celebs/celeb_list.html', {
		'celebs': celebs,
		'categories': categories,
		'countries': countries,
		'selected_category': cat_id,
		'selected_family': family_id,
		'selected_type': type_id,
		'selected_country': country_id,
		'q': q,
	})


def celeb_detail_by_pk(request, pk):
	celeb = get_object_or_404(Celeb, pk=pk)
	return redirect(celeb.get_absolute_url(), permanent=True)


def celeb_detail(request, cat_slug, family_slug, type_slug, slug):
	qs = Celeb.objects.select_related('type__family__category')
	if not request.user.is_staff:
		qs = qs.filter(published=True)
	celeb = get_object_or_404(qs, slug=slug)
	comments = celeb.comments.select_related('user').order_by('-created_at')
	reviews = celeb.reviews.select_related('user').order_by('-created_at')
	followers = celeb.followers.select_related('user').order_by('user__username')
	like_count = celeb.likes.count()
	follow_count = followers.count()
	review_count = reviews.count()
	avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
	user_liked = request.user.is_authenticated and celeb.likes.filter(user=request.user).exists()
	user_following = request.user.is_authenticated and celeb.followers.filter(user=request.user).exists()
	user_review = None
	user_followed_celebs = []
	if request.user.is_authenticated:
		user_review = reviews.filter(user=request.user).first()
		user_followed_celebs = (
			Celeb.objects
			.filter(followers__user=request.user)
			.select_related('type__family__category')
			.order_by('name')
		)
	context = {
		'celeb': celeb,
		'comments': comments,
		'reviews': reviews,
		'like_count': like_count,
		'followers': followers,
		'follow_count': follow_count,
		'review_count': review_count,
		'avg_rating': avg_rating,
		'user_liked': user_liked,
		'user_following': user_following,
		'user_review': user_review,
		'user_followed_celebs': user_followed_celebs,
	}

	# OG / social sharing
	og_image = ''
	if celeb.image:
		img_url = celeb.image.url
		og_image = img_url if img_url.startswith('http') else request.build_absolute_uri(img_url)
	words = celeb.bio.split() if celeb.bio else []
	og_description = (
		' '.join(words[:30]) + ('…' if len(words) > 30 else '')
		if words
		else f'{celeb.name} — {celeb.type.family.category} celebrity on CelebsAfrica.'
	)
	share_url = request.build_absolute_uri(celeb.get_absolute_url())
	context.update({'og_image': og_image, 'og_description': og_description, 'share_url': share_url})

	return render(request, 'celebs/celeb_detail.html', context)


@login_required
def celeb_follow(request, pk):
	celeb = get_object_or_404(Celeb.objects.select_related('type__family__category'), pk=pk)
	if request.method == 'POST':
		follow, created = Follow.objects.get_or_create(celeb=celeb, user=request.user)
		if not created:
			follow.delete()
	return HttpResponseRedirect(celeb.get_absolute_url())


@login_required
def celeb_review(request, pk):
	celeb = get_object_or_404(Celeb.objects.select_related('type__family__category'), pk=pk)
	if request.method == 'POST':
		try:
			rating = int(request.POST.get('rating', 0))
		except ValueError:
			rating = 0
		if 1 <= rating <= 5:
			text = request.POST.get('text', '').strip()
			_, created = Review.objects.update_or_create(
				celeb=celeb, user=request.user,
				defaults={'rating': rating, 'text': text}
			)
			if created:
				messages.success(request, 'Your review has been submitted.')
			else:
				messages.success(request, 'Your review has been updated.')
		else:
			messages.error(request, 'Please select a star rating before submitting.')
	return HttpResponseRedirect(celeb.get_absolute_url() + '#reviews')


@login_required
def celeb_review_delete(request, pk):
	celeb = get_object_or_404(Celeb.objects.select_related('type__family__category'), pk=pk)
	if request.method == 'POST':
		Review.objects.filter(celeb=celeb, user=request.user).delete()
		messages.success(request, 'Your review has been deleted.')
	return HttpResponseRedirect(celeb.get_absolute_url() + '#reviews')


@login_required
def celeb_like(request, pk):
	celeb = get_object_or_404(Celeb.objects.select_related('type__family__category'), pk=pk)
	if request.method == 'POST':
		like, created = Like.objects.get_or_create(celeb=celeb, user=request.user)
		if not created:
			like.delete()
	return HttpResponseRedirect(celeb.get_absolute_url())


@login_required
def celeb_comment(request, pk):
	celeb = get_object_or_404(Celeb.objects.select_related('type__family__category'), pk=pk)
	if request.method == 'POST':
		text = request.POST.get('text', '').strip()
		if text:
			Comment.objects.create(celeb=celeb, user=request.user, text=text)
			messages.success(request, 'Comment posted.')
	return HttpResponseRedirect(celeb.get_absolute_url() + '#comments')


@login_required
def comment_edit(request, pk):
	comment = get_object_or_404(Comment.objects.select_related('celeb__type__family__category'), pk=pk)
	if comment.user != request.user:
		return HttpResponseForbidden('You can only edit your own comments.')
	if request.method == 'POST':
		text = request.POST.get('text', '').strip()
		if text:
			comment.text = text
			comment.save()
			messages.success(request, 'Comment updated.')
		else:
			messages.error(request, 'Comment cannot be empty.')
	return HttpResponseRedirect(comment.celeb.get_absolute_url() + '#comments')


@login_required
def comment_delete(request, pk):
	comment = get_object_or_404(Comment.objects.select_related('celeb__type__family__category'), pk=pk)
	if comment.user != request.user and not request.user.is_staff:
		return HttpResponseForbidden('You do not have permission to delete this comment.')
	celeb_url = comment.celeb.get_absolute_url()
	if request.method == 'POST':
		comment.delete()
		messages.success(request, 'Comment deleted.')
	return HttpResponseRedirect(celeb_url + '#comments')


@staff_required
def celeb_create(request):
	types = Type.objects.select_related('family__category').order_by('family__category__name', 'family__name', 'name')
	countries = Country.objects.all()
	if request.method == 'POST':
		name = request.POST.get('name')
		street_name = request.POST.get('street_name')
		bio = request.POST.get('bio', '')
		discovered = request.POST.get('discovered')
		date_of_birth = request.POST.get('date_of_birth')
		date_of_death = request.POST.get('date_of_death')
		type_id = request.POST.get('type')
		nationality_id = request.POST.get('nationality') or None
		image = request.FILES.get('image')
		new_celeb = Celeb.objects.create(
			name=name,
			street_name=street_name,
			bio=bio,
			type_id=type_id,
			nationality_id=nationality_id,
			discovered=discovered or None,
			date_of_birth=date_of_birth or None,
			date_of_death=date_of_death or None,
			image=image,
			awards=request.POST.get('awards', ''),
			featured_video=request.POST.get('featured_video', ''),
			published=request.POST.get('published') == 'on',
		)
		_save_social_links(request, new_celeb)
		return HttpResponseRedirect(reverse('celebs_home'))
	return render(request, 'celebs/celeb_form.html', {
		'types': types, 'countries': countries,
		'platform_choices': CelebSocialLink.PLATFORM_CHOICES,
	})


@staff_required
def celeb_update(request, slug):
	celeb = get_object_or_404(Celeb, slug=slug)
	types = Type.objects.select_related('family__category').order_by('family__category__name', 'family__name', 'name')
	countries = Country.objects.all()
	if request.method == 'POST':
		celeb.name = request.POST.get('name')
		celeb.street_name = request.POST.get('street_name')
		celeb.bio = request.POST.get('bio', '')
		celeb.type_id = request.POST.get('type')
		celeb.nationality_id = request.POST.get('nationality') or None
		celeb.discovered = request.POST.get('discovered') or None
		celeb.date_of_birth = request.POST.get('date_of_birth') or None
		celeb.date_of_death = request.POST.get('date_of_death') or None
		celeb.awards = request.POST.get('awards', '')
		celeb.featured_video = request.POST.get('featured_video', '')
		celeb.published = request.POST.get('published') == 'on'
		if request.FILES.get('image'):
			celeb.image = request.FILES.get('image')
		celeb.save()
		_save_social_links(request, celeb)
		return HttpResponseRedirect(celeb.get_absolute_url())
	return render(request, 'celebs/celeb_form.html', {
		'celeb': celeb, 'types': types, 'countries': countries,
		'platform_choices': CelebSocialLink.PLATFORM_CHOICES,
	})


@staff_required
def celeb_delete(request, pk):
	celeb = get_object_or_404(Celeb, pk=pk)
	if request.method == 'POST':
		celeb.delete()
		return HttpResponseRedirect(reverse('celebs_home'))
	return render(request, 'celebs/celeb_confirm_delete.html', {'celeb': celeb})


@staff_required
def celeb_photo_upload(request, pk):
	celeb = get_object_or_404(Celeb, pk=pk)
	if request.method == 'POST':
		for f in request.FILES.getlist('photos'):
			CelebPhoto.objects.create(
				celeb=celeb,
				image=f,
				caption=request.POST.get('caption', ''),
			)
	return HttpResponseRedirect(celeb.get_absolute_url() + '#gallery')


@staff_required
def celeb_photo_delete(request, pk):
	photo = get_object_or_404(CelebPhoto, pk=pk)
	celeb = photo.celeb
	if request.method == 'POST':
		photo.image.delete(save=False)
		photo.delete()
	return HttpResponseRedirect(celeb.get_absolute_url() + '#gallery')

