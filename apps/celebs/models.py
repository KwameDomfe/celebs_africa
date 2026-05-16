from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Country(models.Model):
	name = models.CharField(max_length=100, unique=True)
	code = models.CharField(max_length=2, unique=True, help_text='ISO 3166-1 alpha-2 code')
	flag = models.CharField(max_length=10, blank=True, help_text='Flag emoji')

	class Meta:
		verbose_name_plural = 'Countries'
		ordering = ['name']

	def __str__(self):
		return f"{self.flag} {self.name}" if self.flag else self.name


class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=120, unique=True, blank=True)

	class Meta:
		verbose_name_plural = 'Categories'

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Family(models.Model):
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='families')
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=120, blank=True)

	class Meta:
		verbose_name_plural = 'Families'
		unique_together = ('category', 'name')

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.category.name} / {self.name}"


class Type(models.Model):
	family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='types')
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=120, blank=True)

	class Meta:
		unique_together = ('family', 'name')

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.family.category.name} / {self.family.name} / {self.name}"


class Celeb(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=120, unique=True, blank=True)
	type = models.ForeignKey(Type, on_delete=models.PROTECT, related_name='celebs', null=True, blank=True)
	street_name = models.CharField(max_length=50)
	bio = models.TextField(blank=True)
	nationality = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True, blank=True, related_name='celebs')
	rating = models.FloatField(default=0.0, help_text="Legacy field; rating now computed from reviews")
	discovered = models.DateField(null=True, blank=True)
	date_of_birth = models.DateField(null=True, blank=True)
	date_of_death = models.DateField(null=True, blank=True)
	image = models.ImageField(upload_to='celebs/', null=True, blank=True)
	awards = models.TextField(blank=True, help_text='Notable awards and achievements')
	website = models.URLField(max_length=200, blank=True)
	instagram = models.CharField(max_length=100, blank=True, help_text='Username only, no @')
	twitter = models.CharField(max_length=100, blank=True, help_text='Username only, no @')
	facebook = models.CharField(max_length=100, blank=True, help_text='Page name or URL slug')
	youtube = models.CharField(max_length=100, blank=True, help_text='Channel name or URL slug')
	featured_video = models.URLField(max_length=200, blank=True, help_text='YouTube video URL e.g. https://www.youtube.com/watch?v=...')
	published = models.BooleanField(default=True, help_text='Unpublished celebs are hidden from all public listings and detail pages')

	@property
	def is_deceased(self):
		return self.date_of_death is not None

	@property
	def featured_video_embed_url(self):
		"""Convert any YouTube video URL to an embed URL. Returns '' if not a valid video URL."""
		url = self.featured_video.strip()
		if not url:
			return ''
		import re
		video_id = None
		# Already an embed URL
		m = re.search(r'youtube\.com/embed/([A-Za-z0-9_-]+)', url)
		if m:
			video_id = m.group(1)
		if not video_id:
			# youtu.be/VIDEO_ID
			m = re.search(r'youtu\.be/([A-Za-z0-9_-]+)', url)
			if m:
				video_id = m.group(1)
		if not video_id:
			# youtube.com/watch?v=VIDEO_ID
			m = re.search(r'[?&]v=([A-Za-z0-9_-]+)', url)
			if m:
				video_id = m.group(1)
		if not video_id:
			return ''
		# origin param is required by the YouTube player to avoid Error 153
		return f'https://www.youtube.com/embed/{video_id}?origin=https://celebsafrica.com'

	@property
	def age(self):
		if not self.date_of_birth:
			return None
		from datetime import date
		end = self.date_of_death if self.date_of_death else date.today()
		dob = self.date_of_birth
		return end.year - dob.year - ((end.month, end.day) < (dob.month, dob.day))

	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.name)
			slug = base_slug
			n = 1
			while Celeb.objects.filter(slug=slug).exclude(pk=self.pk).exists():
				slug = f"{base_slug}-{n}"
				n += 1
			self.slug = slug
		super().save(*args, **kwargs)

	def get_absolute_url(self):
		from django.urls import reverse
		if self.type_id:
			cat_slug = self.type.family.category.slug
			family_slug = self.type.family.slug
			type_slug = self.type.slug
		else:
			cat_slug = family_slug = type_slug = 'uncategorised'
		return reverse('celeb_detail', args=[cat_slug, family_slug, type_slug, self.slug])

	def __str__(self):
		return self.name


class CelebPhoto(models.Model):
	celeb = models.ForeignKey(Celeb, on_delete=models.CASCADE, related_name='photos')
	image = models.ImageField(upload_to='celebs/gallery/')
	caption = models.CharField(max_length=200, blank=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-uploaded_at']

	def __str__(self):
		return f"{self.celeb.name} photo {self.pk}"


class Like(models.Model):
	celeb = models.ForeignKey(Celeb, on_delete=models.CASCADE, related_name='likes')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='celeb_likes')

	class Meta:
		unique_together = ('celeb', 'user')


class Comment(models.Model):
	celeb = models.ForeignKey(Celeb, on_delete=models.CASCADE, related_name='comments')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='celeb_comments')
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.user.username} on {self.celeb.name}"


class Follow(models.Model):
	celeb = models.ForeignKey(Celeb, on_delete=models.CASCADE, related_name='followers')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

	class Meta:
		unique_together = ('celeb', 'user')

	def __str__(self):
		return f"{self.user.username} follows {self.celeb.name}"


class Review(models.Model):
	RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

	celeb = models.ForeignKey(Celeb, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='celeb_reviews')
	rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
	text = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ('celeb', 'user')

	def __str__(self):
		return f"{self.user.username} rated {self.celeb.name} {self.rating}/5"
