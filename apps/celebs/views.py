
import json
import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Avg
from .models import Celeb, Like, Comment, Family, Type, Category, Follow, Review, Country, CelebPhoto, CelebSocialLink


logger = logging.getLogger(__name__)


def _seo_description(celeb):
	"""Build a concise, keyword-rich description for search engines and social cards."""
	parts = []
	if celeb.bio:
		words = celeb.bio.split()
		parts.append(' '.join(words[:26]) + ('…' if len(words) > 26 else ''))
	else:
		details = []
		if celeb.street_name:
			details.append(celeb.street_name)
		if celeb.type_id:
			details.append(str(celeb.type))
		if celeb.nationality:
			details.append(celeb.nationality.name)
		base = f"{celeb.name} is a {' '.join(details) if details else 'featured celebrity'} on CelebsAfrica."
		parts.append(base)
	if celeb.awards:
		award_words = celeb.awards.split()
		parts.append('Awards: ' + ' '.join(award_words[:14]) + ('…' if len(award_words) > 14 else ''))
	return ' '.join(parts)

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

def _person_schema(celeb, page_url, image_url, avg_rating, review_count, follow_count):
	"""Build JSON-LD Person data for the celeb profile page."""
	schema = {
		'@context': 'https://schema.org',
		'@type': 'Person',
		'name': celeb.name,
		'url': page_url,
		'mainEntityOfPage': page_url,
	}
	if celeb.street_name:
		schema['alternateName'] = celeb.street_name
	if image_url:
		schema['image'] = image_url
	if celeb.date_of_birth:
		schema['birthDate'] = celeb.date_of_birth.isoformat()
	if celeb.date_of_death:
		schema['deathDate'] = celeb.date_of_death.isoformat()
	if celeb.nationality:
		schema['nationality'] = {
			'@type': 'Country',
			'name': celeb.nationality.name,
		}
	if celeb.type_id:
		schema['jobTitle'] = celeb.type.name
		schema['knowsAbout'] = [
			celeb.type.family.category.name,
			celeb.type.family.name,
			celeb.type.name,
		]
	if celeb.bio:
		schema['description'] = celeb.bio[:500]
	if avg_rating is not None and review_count > 0:
		schema['aggregateRating'] = {
			'@type': 'AggregateRating',
			'ratingValue': round(float(avg_rating), 2),
			'ratingCount': review_count,
			'bestRating': 5,
			'worstRating': 1,
		}
	if follow_count > 0:
		schema['interactionStatistic'] = [{
			'@type': 'InteractionCounter',
			'interactionType': {'@type': 'FollowAction'},
			'userInteractionCount': follow_count,
		}]
	return json.dumps(schema, ensure_ascii=True)

@login_required
def celebs_home(request):
	categories = Category.objects.prefetch_related('families__types').order_by('name')
	countries = Country.objects.all()
	celebs = Celeb.objects.filter(published=True).select_related('type__family__category').annotate(
		follower_count=Count('followers', distinct=True),
		avg_rating=Avg('reviews__rating', distinct=True),
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
		'can_manage_any': request.user.has_perm('celebs.add_celeb'),
		'managed_celeb_pks': (
			None  # sentinel: staff can manage all
			if request.user.is_authenticated and request.user.is_staff
			else set(request.user.managed_celebs.values_list('pk', flat=True))
			if request.user.is_authenticated
			else set()
		),
	})

@login_required
def celeb_detail_by_pk(request, pk):
	celeb = get_object_or_404(Celeb, pk=pk)
	return redirect(celeb.get_absolute_url(), permanent=True)

@login_required
def celeb_detail(request, cat_slug, family_slug, type_slug, slug):
	qs = Celeb.objects.select_related('type__family__category')
	celeb = get_object_or_404(qs, slug=slug)
	if not celeb.published and not request.user.has_perm('celebs.change_celeb', celeb):
		from django.http import Http404
		raise Http404
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
	published_qs = Celeb.objects.filter(published=True).select_related('type__family__category')
	prev_celeb = published_qs.filter(name__lt=celeb.name).order_by('-name').first()
	next_celeb = published_qs.filter(name__gt=celeb.name).order_by('name').first()

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
		'can_manage': request.user.has_perm('celebs.change_celeb', celeb),
		'prev_celeb': prev_celeb,
		'next_celeb': next_celeb,
	}

	# OG / social sharing
	og_image = ''
	if celeb.image:
		img_url = celeb.image.url
		og_image = img_url if img_url.startswith('http') else request.build_absolute_uri(img_url)
	og_description = _seo_description(celeb)
	share_url = request.build_absolute_uri(celeb.get_absolute_url())
	person_schema_json = _person_schema(
		celeb=celeb,
		page_url=share_url,
		image_url=og_image,
		avg_rating=avg_rating,
		review_count=review_count,
		follow_count=follow_count,
	)
	context.update({
		'og_image': og_image,
		'og_description': og_description,
		'share_url': share_url,
		'person_schema_json': person_schema_json,
	})

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
		raise PermissionDenied
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
	if comment.user != request.user and not request.user.has_perm('celebs.change_celeb', comment.celeb):
		raise PermissionDenied
	celeb_url = comment.celeb.get_absolute_url()
	if request.method == 'POST':
		comment.delete()
		messages.success(request, 'Comment deleted.')
	return HttpResponseRedirect(celeb_url + '#comments')

@permission_required('celebs.add_celeb', raise_exception=True)
def celeb_create(request):
	types = Type.objects.select_related('family__category').order_by('family__category__name', 'family__name', 'name')
	countries = Country.objects.all()
	if request.method == 'POST':
		name = (request.POST.get('name') or '').strip()
		street_name = (request.POST.get('street_name') or '').strip()
		bio = request.POST.get('bio', '')
		discovered = request.POST.get('discovered')
		date_of_birth = request.POST.get('date_of_birth')
		date_of_death = request.POST.get('date_of_death')
		type_id = (request.POST.get('type') or '').strip()
		nationality_id = request.POST.get('nationality') or None
		image = request.FILES.get('image')

		# Avoid production 500s on malformed/empty required fields.
		errors = []
		if not name:
			errors.append('Name is required.')
		if not street_name:
			errors.append('Street name is required.')
		if not type_id:
			errors.append('Category / Family / Type is required.')

		if errors:
			for err in errors:
				messages.error(request, err)
			return render(request, 'celebs/celeb_form.html', {
				'types': types,
				'countries': countries,
				'platform_choices': CelebSocialLink.PLATFORM_CHOICES,
			})

		try:
			with transaction.atomic():
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
				# Auto-add non-staff creators as managers so they can edit their own celeb
				if not request.user.is_staff:
					new_celeb.managers.add(request.user)
		except Exception:
			logger.exception('Celeb create failed for user=%s', request.user.pk)
			messages.error(
				request,
				'Could not create celeb right now. Please try again, or remove the image and retry.',
			)
			return render(request, 'celebs/celeb_form.html', {
				'types': types,
				'countries': countries,
				'platform_choices': CelebSocialLink.PLATFORM_CHOICES,
			})

		messages.success(request, 'Celeb created successfully.')
		return HttpResponseRedirect(new_celeb.get_absolute_url())
	return render(request, 'celebs/celeb_form.html', {
		'types': types, 'countries': countries,
		'platform_choices': CelebSocialLink.PLATFORM_CHOICES,
	})

@login_required
def celeb_update(request, slug):
	celeb = get_object_or_404(Celeb, slug=slug)
	if not request.user.has_perm('celebs.change_celeb', celeb):
		raise PermissionDenied
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

@login_required
def celeb_delete(request, pk):
	celeb = get_object_or_404(Celeb, pk=pk)
	if not request.user.has_perm('celebs.delete_celeb', celeb):
		raise PermissionDenied
	if request.method == 'POST':
		celeb.delete()
		return HttpResponseRedirect(reverse('celebs_home'))
	return render(request, 'celebs/celeb_confirm_delete.html', {'celeb': celeb})

@login_required
def celeb_photo_upload(request, pk):
	celeb = get_object_or_404(Celeb, pk=pk)
	if not request.user.has_perm('celebs.change_celeb', celeb):
		raise PermissionDenied
	if request.method == 'POST':
		for f in request.FILES.getlist('photos'):
			CelebPhoto.objects.create(
				celeb=celeb,
				image=f,
				caption=request.POST.get('caption', ''),
			)
	return HttpResponseRedirect(celeb.get_absolute_url() + '#gallery')

@login_required
def celeb_photo_delete(request, pk):
	photo = get_object_or_404(CelebPhoto, pk=pk)
	celeb = photo.celeb
	if not request.user.has_perm('celebs.change_celeb', celeb):
		raise PermissionDenied
	if request.method == 'POST':
		photo.image.delete(save=False)
		photo.delete()
	return HttpResponseRedirect(celeb.get_absolute_url() + '#gallery')

@login_required
def my_celebs(request):
	if request.user.is_staff:
		qs = Celeb.objects.select_related('type__family__category').order_by('name')
	else:
		qs = (
			request.user.managed_celebs
			.select_related('type__family__category')
			.order_by('name')
		)

	published_celebs = qs.filter(published=True)
	unpublished_celebs = qs.filter(published=False)

	return render(request, 'celebs/my_celebs.html', {
		'published_celebs': published_celebs,
		'unpublished_celebs': unpublished_celebs,
		'can_create': request.user.has_perm('celebs.add_celeb'),
	})
