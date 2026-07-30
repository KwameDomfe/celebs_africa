from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.safestring import mark_safe


def _si(path):
	"""Wrap an SVG path in a standard 18×18 inline SVG element."""
	return mark_safe(
		'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
		'width="18" height="18" fill="currentColor">'
		f'<path d="{path}"/></svg>'
	)


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
	influence = models.TextField(blank=True, null=True, help_text='Notable influence, impact, or legacy')
	net_worth = models.DecimalField(
		max_digits=15, 
		decimal_places=2, 
		null=True, 
		blank=True, 
		help_text='Estimated net worth in USD')
	nationality = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True, blank=True, related_name='celebs')
	spouse = models.CharField(max_length=100, 
		blank=True, 
		null=True, 
		help_text='Name of spouse or partner',
	)
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
	managers = models.ManyToManyField(
		User, blank=True, related_name='managed_celebs',
		help_text='Users (celebs/managers) who can edit this celeb page',
	)

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

	def _build_unique_slug(self):
		"""Build a readable, mostly-stable unique slug for this celeb."""
		candidates = []
		name_slug = slugify(self.name) if self.name else ''
		street_slug = slugify(self.street_name) if self.street_name else ''

		if name_slug:
			candidates.append(name_slug)
		if name_slug and street_slug and street_slug != name_slug:
			candidates.append(f"{name_slug}-{street_slug}")

		base_slug = next((cand for cand in candidates if cand), '')
		if not base_slug:
			base_slug = f"celeb-{self.pk}" if self.pk else 'celeb'

		for cand in candidates:
			if not cand:
				continue
			if not Celeb.objects.filter(slug=cand).exclude(pk=self.pk).exists():
				return cand

		n = 1
		slug = f"{base_slug}-{n}"
		while Celeb.objects.filter(slug=slug).exclude(pk=self.pk).exists():
			n += 1
			slug = f"{base_slug}-{n}"
		return slug

	def save(self, *args, **kwargs):
		should_refresh_slug = False
		if not self.pk:
			should_refresh_slug = True
		else:
			old = Celeb.objects.filter(pk=self.pk).values('name', 'street_name').first()
			if old:
				if (old['name'] != self.name) or (old['street_name'] != self.street_name):
					should_refresh_slug = True

		if should_refresh_slug or not self.slug:
			self.slug = self._build_unique_slug()
		super().save(*args, **kwargs)

	def get_absolute_url(self):
		from django.urls import reverse
		# Some legacy rows may have an empty slug; backfill a unique value on demand
		# so URL reversing and detail routing remain stable.
		if not self.slug:
			slug = self._build_unique_slug()
			if self.pk:
				Celeb.objects.filter(pk=self.pk).update(slug=slug)
			self.slug = slug
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


class CelebSocialLink(models.Model):
	PLATFORM_CHOICES = [
		('website',     'Website'),
		('instagram',   'Instagram'),
		('twitter',     'Twitter / X'),
		('facebook',    'Facebook'),
		('tiktok',      'TikTok'),
		('youtube',     'YouTube'),
		('snapchat',    'Snapchat'),
		('threads',     'Threads'),
		('linkedin',    'LinkedIn'),
		('spotify',     'Spotify'),
		('soundcloud',  'SoundCloud'),
		('apple_music', 'Apple Music'),
		('deezer',      'Deezer'),
		('audiomack',   'Audiomack'),
		('boomplay',    'Boomplay'),
		('telegram',    'Telegram'),
		('whatsapp',    'WhatsApp'),
		('twitch',      'Twitch'),
		('vimeo',       'Vimeo'),
		('pinterest',   'Pinterest'),
		('other',       'Other'),
	]
	_ICONS = {
		'website':     (_si('M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 18c-.918 0-1.846-.15-2.75-.45C8.124 16.548 7 14.38 7 12s1.124-4.548 2.25-7.55A9.956 9.956 0 0112 4c.956 0 1.887.133 2.75.45C15.876 7.452 17 9.62 17 12s-1.124 4.548-2.25 7.55A9.956 9.956 0 0112 20zm-7.95-6H2.05a9.956 9.956 0 000-4h2c-.033.66-.05 1.325-.05 2s.017 1.34.05 2zm1.544 2H3.17a9.978 9.978 0 005.38 3.95C7.673 18.36 6.946 17.11 6.3 16 6.1 15.68 5.9 15.35 5.72 15zm12.56 0c-.18.35-.38.68-.58 1-.646 1.11-1.373 2.36-2.25 3.95A9.978 9.978 0 0020.83 16h-2.55zM19.95 14H22a9.956 9.956 0 000-4h-2.05c.033.66.05 1.325.05 2s-.017 1.34-.05 2zm-.78-6h2.46a9.978 9.978 0 00-5.38-3.95C17.027 5.64 17.754 6.89 18.4 8c.2.32.4.65.58 1H19.17zM5.72 9c.18-.35.38-.68.58-1C6.946 6.89 7.673 5.64 8.55 4.05A9.978 9.978 0 003.17 8H5.72z'), '#8af'),
		'instagram':   (_si('M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z'), '#e1a'),
		'twitter':     (_si('M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.26 5.632zm-1.161 17.52h1.833L7.084 4.126H5.117z'), '#aaa'),
		'facebook':    (_si('M24 12.073C24 5.404 18.627 0 12 0S0 5.404 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.236 2.686.236v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.267h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z'), '#4267B2'),
		'tiktok':      (_si('M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z'), '#aaa'),
		'youtube':     (_si('M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z'), '#f00'),
		'snapchat':    (_si('M12.206.793c.99 0 4.347.276 5.93 3.821.529 1.193.403 3.219.299 4.847l-.003.06c-.012.18-.028.37-.042.53.032.019.063.027.095.027.189 0 .396-.196.633-.196.201 0 .771.128.808.577.049.26-.061.486-.357.701-.02.015-.048.029-.075.044-.257.155-.557.307-.792.656-.115.17-.11.301.019.439.181.195 1.028.913 1.028 2.1 0 .913-.577 1.566-1.157 2.148-.457.458-.876.812-1.002 1.188-.091.274-.031.457.112.74.205.432 1.215 1.014 2.09 1.528.262.157.523.312.773.474.65.424 1.02.793.786 1.329-.141.321-.541.632-1.255.633l-.029.001c-1.099 0-2.218-.483-2.882-.862-.197-.113-.371-.23-.498-.33-.038-.028-.097-.054-.153-.054-.047 0-.102.021-.145.054-.101.092-.219.212-.362.344-.537.487-1.279 1.154-2.533 1.154-.089 0-.18-.004-.271-.013-.029.005-.06.007-.09.007-.024 0-.047-.002-.07-.005l-.009.001c-1.255 0-1.997-.667-2.534-1.154-.143-.132-.261-.252-.362-.344-.043-.033-.098-.054-.145-.054-.056 0-.115.026-.153.054-.128.1-.301.217-.498.33-.664.379-1.783.862-2.882.862l-.029-.001c-.714-.001-1.114-.312-1.255-.633-.234-.536.136-.905.786-1.329.25-.162.511-.317.773-.474.875-.514 1.885-1.096 2.09-1.528.143-.283.203-.466.112-.74-.126-.376-.545-.73-1.002-1.188-.58-.582-1.157-1.235-1.157-2.148 0-1.187.847-1.905 1.028-2.1.129-.138.134-.269.019-.439-.235-.349-.535-.501-.792-.656-.027-.015-.055-.029-.075-.044-.296-.215-.406-.441-.357-.701.037-.449.607-.577.808-.577.232 0 .439.196.633.196.032 0 .063-.008.095-.027l-.042-.53-.003-.06c-.104-1.628-.23-3.654.299-4.847C7.859 1.069 11.216.793 12.206.793z'), '#f5f'),
		'threads':     (_si('M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.964-.065-1.19.408-2.285 1.33-3.082.88-.76 2.119-1.207 3.583-1.291a13.853 13.853 0 012.099.048c-.093-.62-.27-1.089-.545-1.398-.426-.487-1.112-.739-2.039-.75h-.056c-.72 0-1.886.199-2.592 1.525l-1.765-1.069C6.33 7.217 7.85 6.394 9.611 6.337a6.797 6.797 0 01.18-.003c1.555 0 2.916.556 3.836 1.567.602.658.985 1.517 1.14 2.556a11.23 11.23 0 011.591.503c1.975.84 3.244 2.354 3.337 4.259.128 2.594-.953 5.063-2.965 6.647-1.656 1.321-3.783 2.134-6.554 2.134zm.057-9.099c-.52.03-.982.147-1.327.35-.386.226-.571.524-.546.882.022.313.199.578.501.771.351.228.824.343 1.317.315 1.072-.059 1.82-.524 2.223-1.384.198-.425.309-.94.33-1.541a10.178 10.178 0 00-2.498-.393z'), '#aaa'),
		'linkedin':    (_si('M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z'), '#0A66C2'),
		'spotify':     (_si('M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z'), '#1DB954'),
		'soundcloud':  (_si('M11.56 8.87V17h8.76c1.47-.01 2.68-1.2 2.68-2.68a2.68 2.68 0 00-2.38-2.67 4.48 4.48 0 00-4.44-4.99 4.48 4.48 0 00-4.62 2.21zM0 14.46c0 1.4 1.14 2.54 2.55 2.54S5.1 15.86 5.1 14.46 3.96 11.92 2.55 11.92 0 13.06 0 14.46zm5.68-1.41c-.14-.77-.2-1.53-.17-2.21.03-.68.14-1.28.3-1.76a4.84 4.84 0 00-1.3-.18c-.5 0-.98.07-1.4.2.38 1.18.58 2.51.58 3.95zm1.5-4.4c.3-.5.68-.92 1.12-1.25a4.83 4.83 0 00-2.04-.45 4.84 4.84 0 00-1.76.33 6.92 6.92 0 011.37 1.78 4.84 4.84 0 011.31-.41zm-1.04 4.4c-.02-.66.05-1.38.2-2.1a4.84 4.84 0 01-1.65.29 4.84 4.84 0 01-1.07-.12 2.54 2.54 0 011.1 2.12c0 .05 0 .1-.01.15.48.09.97.09 1.43-.34z'), '#FF5500'),
		'apple_music': (_si('M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm4 15.25a.75.75 0 01-.75.75h-6.5a.75.75 0 010-1.5H11V9.604l-2.386.795a.75.75 0 01-.472-1.423l3-1a.75.75 0 01.972.713V14.5h1.136A.75.75 0 0116 15.25z'), '#FC3C44'),
		'deezer':      (_si('M14.81 3.656h2.356v16.485H14.81zm-4.756.85h2.356v15.635H10.054zm-4.757 2.831H7.65v12.803H5.297zM.54 10.17h2.356v6.302H.54zm19.163-6.514h2.356v16.485H19.703z'), '#00C7F2'),
		'audiomack':   (_si('M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm-1.5 16.5v-9l7 4.5-7 4.5z'), '#FF6600'),
		'boomplay':    (_si('M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm-2 16V8l7 4-7 4z'), '#f60'),
		'telegram':    (_si('M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z'), '#26A5E4'),
		'whatsapp':    (_si('M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z'), '#25D366'),
		'twitch':      (_si('M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714z'), '#9146FF'),
		'vimeo':       (_si('M23.977 6.416c-.105 2.338-1.739 5.543-4.894 9.609-3.268 4.247-6.026 6.37-8.29 6.37-1.409 0-2.578-1.294-3.553-3.881L5.322 11.4C4.603 8.816 3.834 7.522 3.01 7.522c-.179 0-.806.378-1.881 1.132L0 7.197c1.185-1.044 2.351-2.084 3.501-3.128C5.08 2.701 6.266 1.984 7.055 1.91c1.867-.18 3.016 1.1 3.447 3.838.465 2.953.789 4.789.971 5.507.539 2.45 1.131 3.674 1.776 3.674.502 0 1.256-.796 2.265-2.385 1.004-1.589 1.54-2.797 1.612-3.628.144-1.371-.395-2.061-1.612-2.061-.574 0-1.167.121-1.777.391 1.186-3.868 3.434-5.757 6.762-5.637 2.473.06 3.628 1.664 3.484 4.797z'), '#1ab7ea'),
		'pinterest':   (_si('M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 010 .345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.632-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0z'), '#E60023'),
		'other':       (_si('M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71'), '#888'),
	}

	celeb = models.ForeignKey(Celeb, on_delete=models.CASCADE, related_name='social_links')
	platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
	url = models.URLField(max_length=500)
	order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ['order', 'platform']

	def get_icon(self):
		return self._ICONS.get(self.platform, ('🔗', '#888'))[0]

	def get_color(self):
		return self._ICONS.get(self.platform, ('🔗', '#888'))[1]

	def __str__(self):
		return f"{self.celeb.name} — {self.get_platform_display()}"


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
