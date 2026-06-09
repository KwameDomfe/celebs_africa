from urllib.parse import quote_plus

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.images import get_image_dimensions
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render

from .models import Post, PostComment, PostLike, PostShare


MAX_POST_IMAGE_BYTES = 5 * 1024 * 1024
MAX_POST_IMAGE_WIDTH = 4096
MAX_POST_IMAGE_HEIGHT = 4096


def _validate_post_image(image):
    if not image:
        return None
    if image.size > MAX_POST_IMAGE_BYTES:
        return 'Image is too large. Maximum size is 5MB.'
    try:
        width, height = get_image_dimensions(image)
    except Exception:
        return 'Uploaded file is not a valid image.'
    if width > MAX_POST_IMAGE_WIDTH or height > MAX_POST_IMAGE_HEIGHT:
        return 'Image dimensions are too large. Maximum is 4096x4096 pixels.'
    return None


@login_required
def posts_home(request):
    posts_qs = (
        Post.objects.filter(is_deleted=False).select_related('user', 'user__profile')
        .annotate(
            like_count=Count('likes', distinct=True),
            comment_count=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
            share_count=Count('shares', distinct=True),
        )
        .prefetch_related(
            Prefetch(
                'comments',
                queryset=PostComment.objects.filter(is_deleted=False).select_related('user', 'user__profile').order_by('created_at'),
            )
        )
    )
    posts = list(posts_qs)
    liked_post_ids = set(
        PostLike.objects.filter(user=request.user, post_id__in=[post.pk for post in posts]).values_list('post_id', flat=True)
    )
    deleted_posts = Post.objects.filter(user=request.user, is_deleted=True).order_by('-deleted_at')
    deleted_comments = (
        PostComment.objects.filter(user=request.user, is_deleted=True, post__is_deleted=False)
        .select_related('post')
        .order_by('-deleted_at')
    )
    return render(
        request,
        'posts/posts_home.html',
        {
            'posts': posts,
            'liked_post_ids': liked_post_ids,
            'deleted_posts': deleted_posts,
            'deleted_comments': deleted_comments,
        },
    )


@login_required
def post_create(request):
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        image = request.FILES.get('image')
        image_error = _validate_post_image(image)
        if image_error:
            messages.error(request, image_error)
            return redirect('posts_home')
        if text or image:
            Post.objects.create(user=request.user, text=text, image=image)
            messages.success(request, 'Post created.')
        else:
            messages.error(request, 'Write something or upload an image before posting.')
    return redirect('posts_home')


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk, user=request.user, is_deleted=False)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        image = request.FILES.get('image')
        remove_image = request.POST.get('remove_image') == 'on'
        image_error = _validate_post_image(image)
        if image_error:
            messages.error(request, image_error)
            return HttpResponseRedirect(post.get_absolute_url())
        if text or image or (post.image and not remove_image):
            post.text = text
            update_fields = ['text', 'updated_at']
            if remove_image and post.image:
                post.image.delete(save=False)
                post.image = None
                update_fields.append('image')
            elif image:
                post.image = image
                update_fields.append('image')
            post.save(update_fields=update_fields)
            messages.success(request, 'Post updated.')
        else:
            messages.error(request, 'Post cannot be empty. Add text or an image.')
    return HttpResponseRedirect(post.get_absolute_url())


@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, user=request.user, is_deleted=False)
    if request.method == 'POST':
        post.is_deleted = True
        post.deleted_at = timezone.now()
        post.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(request, 'Post moved to trash.')
        return redirect('posts_home')
    return HttpResponseRedirect(post.get_absolute_url())


@login_required
def post_restore(request, pk):
    post = get_object_or_404(Post, pk=pk, user=request.user, is_deleted=True)
    if request.method == 'POST':
        post.is_deleted = False
        post.deleted_at = None
        post.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(request, 'Post restored.')
    return HttpResponseRedirect(post.get_absolute_url())


@login_required
def post_like(request, pk):
    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    if request.method == 'POST':
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
    return HttpResponseRedirect(post.get_absolute_url())


@login_required
def post_comment(request, pk):
    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            PostComment.objects.create(post=post, user=request.user, text=text)
            messages.success(request, 'Comment posted.')
        else:
            messages.error(request, 'Comment cannot be empty.')
    return HttpResponseRedirect(post.get_absolute_url())


@login_required
def post_comment_edit(request, pk):
    comment = get_object_or_404(PostComment, pk=pk, user=request.user, is_deleted=False, post__is_deleted=False)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            comment.text = text
            comment.save(update_fields=['text', 'updated_at'])
            messages.success(request, 'Comment updated.')
        else:
            messages.error(request, 'Comment cannot be empty.')
    return HttpResponseRedirect(comment.post.get_absolute_url())


@login_required
def post_comment_delete(request, pk):
    comment = get_object_or_404(PostComment, pk=pk, user=request.user, is_deleted=False)
    post = comment.post
    if request.method == 'POST':
        comment.is_deleted = True
        comment.deleted_at = timezone.now()
        comment.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(request, 'Comment moved to trash.')
    return HttpResponseRedirect(post.get_absolute_url())


@login_required
def post_comment_restore(request, pk):
    comment = get_object_or_404(PostComment, pk=pk, user=request.user, is_deleted=True, post__is_deleted=False)
    if request.method == 'POST':
        comment.is_deleted = False
        comment.deleted_at = None
        comment.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(request, 'Comment restored.')
    return HttpResponseRedirect(comment.post.get_absolute_url())


@login_required
def post_share(request, pk, platform):
    post = get_object_or_404(Post, pk=pk, is_deleted=False)
    valid_platforms = {
        PostShare.PLATFORM_FACEBOOK,
        PostShare.PLATFORM_TWITTER,
        PostShare.PLATFORM_WHATSAPP,
        PostShare.PLATFORM_TELEGRAM,
    }
    if platform not in valid_platforms:
        return HttpResponseRedirect(post.get_absolute_url())

    PostShare.objects.create(post=post, user=request.user, platform=platform)

    post_url = quote_plus(request.build_absolute_uri(post.get_absolute_url()))
    post_text = quote_plus(post.text[:120])

    targets = {
        PostShare.PLATFORM_FACEBOOK: f'https://www.facebook.com/sharer/sharer.php?u={post_url}',
        PostShare.PLATFORM_TWITTER: f'https://twitter.com/intent/tweet?url={post_url}&text={post_text}',
        PostShare.PLATFORM_WHATSAPP: f'https://wa.me/?text={post_text}%20{post_url}',
        PostShare.PLATFORM_TELEGRAM: f'https://t.me/share/url?url={post_url}&text={post_text}',
    }
    return redirect(targets[platform])
