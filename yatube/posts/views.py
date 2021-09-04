from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PAGINATOR_OBJ_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts_list = group.posts.all()
    paginator = Paginator(group_posts_list, settings.PAGINATOR_OBJ_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_post_list = Post.objects.filter(author__username=username)
    paginator = Paginator(user_post_list, settings.PAGINATOR_OBJ_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    qs = Follow.objects.filter(user_id=request.user.id, author_id=author.id)
    if str(request.user) == username:
        self_follow = True
    else:
        self_follow = False
    if request.user.id in qs.values_list('user_id', flat=True):
        following = True
    else:
        following = False
    context = {
        'self_follow': self_follow,
        'following': following,
        'user_post_list': user_post_list,
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post__id=post_id)
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user)
        return render(request, 'posts/create_post.html',
                      {'form': form})
    context = {
        'form': form,
        'title': 'Новый пост',
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    selected_post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=selected_post
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id=post.pk)
        return render(request,
                      'posts/create_post.html',
                      {'form': form},
                      )
    context = {
        'form': form,
        'title': 'Редактировать пост',
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.PAGINATOR_OBJ_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username).id
    if str(request.user) == username:
        return redirect('posts:profile', username=username)
    else:
        Follow.objects.get_or_create(user_id=request.user.id, author_id=author)
        return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username).id
    Follow.objects.get(user_id=request.user.id, author_id=author).delete()
    return redirect('posts:profile', username=username)
