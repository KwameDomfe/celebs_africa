from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django import forms
import json

from .models import FunnelEvent


ALLOWED_TRACK_EVENTS = {
    FunnelEvent.EVENT_HERO_REGISTER_CLICK,
    FunnelEvent.EVENT_UNLOCK_REGISTER_CLICK,
    FunnelEvent.EVENT_DIRECTORY_GATE_REGISTER_CLICK,
}


def _record_funnel_event(request, event_name, source_path='', metadata=None):
    if metadata is None:
        metadata = {}
    if not request.session.session_key:
        request.session.save()
    FunnelEvent.objects.create(
        event_name=event_name,
        source_path=(source_path or request.path)[:300],
        metadata=metadata,
        session_key=request.session.session_key or '',
        user=request.user if request.user.is_authenticated else None,
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=[
            ('fan', 'Fan'),
            ('celeb', 'Celeb'),
            ('manager', 'Celeb Manager'),
            ('staff', 'Staff'),
        ],
        required=True,
        initial='fan',
        label='I am a',
    )

    class Meta(UserCreationForm.Meta):
        fields = ('username', 'email', 'password1', 'password2')
        field_order = ['username', 'email', 'password1', 'password2', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('account_home')
        return super().dispatch(request, *args, **kwargs)


def account_home(request):
    return render(request, 'accounts/account_home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('account_home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.profile.role = form.cleaned_data['role']
            user.profile.save()
            _record_funnel_event(
                request,
                FunnelEvent.EVENT_SIGNUP_SUCCESS,
                source_path=request.path,
                metadata={'role': form.cleaned_data['role']},
            )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('account_home')
    else:
        form = RegisterForm()
        _record_funnel_event(request, FunnelEvent.EVENT_REGISTER_PAGE_VIEW, source_path=request.path)
    return render(request, 'accounts/register.html', {'form': form})


@csrf_exempt
@require_POST
def track_event(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)

    event_name = payload.get('event', '').strip()
    if event_name not in ALLOWED_TRACK_EVENTS:
        return JsonResponse({'ok': False, 'error': 'invalid_event'}, status=400)

    source_path = payload.get('path') or request.path
    metadata = payload.get('meta') if isinstance(payload.get('meta'), dict) else {}
    _record_funnel_event(request, event_name, source_path=source_path, metadata=metadata)
    return JsonResponse({'ok': True})


@login_required
def profile(request):
    from apps.celebs.models import Like, Comment, Follow
    likes = Like.objects.filter(user=request.user).select_related('celeb__type__family__category').order_by('-id')
    comments = Comment.objects.filter(user=request.user).select_related('celeb__type__family__category').order_by('-created_at')
    following = Follow.objects.filter(user=request.user).select_related('celeb__type__family__category').order_by('celeb__name')
    return render(request, 'accounts/profile.html', {'likes': likes, 'comments': comments, 'following': following})


@login_required
def profile_edit(request):
    user = request.user
    profile = user.profile
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()
        profile.bio = request.POST.get('bio', '').strip()
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']
        profile.save()
        return redirect('profile')
    return render(request, 'accounts/profile_edit.html', {'u': user, 'profile': profile})


@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})

