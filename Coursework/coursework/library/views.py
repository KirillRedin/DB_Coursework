#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib import auth
from django.template import Context
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import update_session_auth_hash
from dbconnect import DataBase
import time
# Create your views here.

db = DataBase()

def login(request):
    error = ""
    if request.method == "GET":
        return render(request, 'registration/login.html')
    else:
        username = request.POST['name']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return redirect('/online_library')
        else:
            error = "Невірне ім'я користувача або пароль"
            return render(request, 'registration/login.html', {"error": error})

def logout(request):
    auth.logout(request)
    return redirect('/login')

def register(request):
    success_message = ""
    pass_error = ""
    user_error = ""

    if request.method == 'POST':
        name = request.POST['name']
        password = request.POST['password']
        r_password = request.POST['r_password']
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            user = None
        if name != "" and password != "" and r_password != "" and password == r_password and user == None:
            user = User.objects.create_user(name, '', password)
            user.save()
            success_message = "Реєстрація пройшла успішно"
        else:
            if password != r_password and r_password != "":
                pass_error = "Паролі не співпадають"
            if user != None:
                user_error = "Користувач з таким ім'ям вже зареєстрований!"

    return render(request, 'registration/register.html',
                          {'success_message': success_message, 'pass_error': pass_error, 'user_error': user_error})

def change_active(request, id):
    user = User.objects.get(id=id)
    current_user = request.user
    if current_user.is_superuser and not user.is_superuser:
        user.is_active = not user.is_active
        user.save()
    return redirect('/online_library/profile/'+id)

def mainpage(request):
    est_time = ""
    cache = ""
    search_by = ""
    current_user = request.user

    if request.method == 'GET':
        all_books = db.get_books_list()
    else:
        title_phrase = request.POST['title_phrase']
        author_phrase = request.POST['author_phrase']
        section_name = request.POST['section_name']
        if title_phrase != '' and author_phrase == '' and section_name == '':
            all_books = db.search_by_title(title_phrase)
        elif author_phrase != '' and title_phrase == '' and section_name == '':
            all_books = db.search_by_author(author_phrase)
        elif section_name != '' and title_phrase == '' and author_phrase == '':
            cache = db.chk_cache(section_name)
            s_time = time.time()
            all_books = db.search_by_section(section_name)
            f_time = time.time() - s_time
            est_time = str(f_time) + ' seconds'
            search_by = 'Tag: Section'
        else:
            all_books = db.search_books(title_phrase, author_phrase, section_name)

    sections = db.get_sections_list()

    p = Paginator(all_books, 10)

    page = request.GET.get('page')
    try:
        books = p.page(page)
    except PageNotAnInteger:
        books = p.page(1)
    except EmptyPage:
        books = p.page(p.num_pages)
    return render(request, 'mainpage.html', {'books': books, 'sections': sections, 'current_user': current_user,
                                             'time': est_time, 'cache': cache, 'param': search_by, 'count': str(len(all_books)) + ' results'})

def author_page(request, author_name):
    sections = db.get_sections_list()
    current_user = request.user

    cache = db.chk_cache(author_name)
    s_time = time.time()
    all_books = db.author_search(author_name)
    f_time = time.time() - s_time
    est_time = str(f_time) + ' seconds'
    search_by = 'Tag: Author'
    p = Paginator(all_books, 10)

    page = request.GET.get('page')
    try:
        books = p.page(page)
    except PageNotAnInteger:
        books = p.page(1)
    except EmptyPage:
        books = p.page(p.num_pages)
    return render(request, 'mainpage.html', {'books': books, 'sections': sections, 'current_user': current_user,
                                             'time': est_time, 'cache': cache, 'param': search_by, 'count': str(len(all_books)) + ' results'})

@staff_member_required
def add_page(request):
    sections = db.get_sections_list()
    if request.method == 'POST':
        title = request.POST['title']
        author = request.POST['author']
        section_name = request.POST['section_name']
        description = request.POST['description']
        book_file = request.FILES['book_file']
        image_file = request.FILES['image_file']
        result = db.add_book(title, author, section_name, description, book_file, image_file)
        return render(request, 'add_page.html',
                      {'title': result[0], 'author': result[1], 'uploaded_book_url': result[2],
                       'uploaded_image_url': result[3], 'sections': sections})
    return render(request, 'add_page.html', {'sections': sections})

@login_required
def add_favorite_page(request, id):
    user = request.user
    if db.is_in_favorite(user, id):
        db.remove_from_favorite(user, id)
    else:
        db.add_to_favorite(user, id)
    return  redirect('/online_library/book/'+id)


@staff_member_required
def edit_page(request, id):
    sections = db.get_sections_list()
    book = db.find_one_book(id)

    if request.method == 'POST':
        try:
            book_file = request.FILES['book_file']
        except:
            book_file = "none"
        try:
            image_file = request.FILES['image_file']
        except:
            image_file = "none"

        title = request.POST['title']
        author = request.POST['author']
        section_name = request.POST['section_name']
        description = request.POST['description']
        db.edit_book(book, title, author, section_name, description, book_file, image_file)
        return redirect('/online_library/admin/edit_book/'+id)

    return render(request, 'edit_page.html', {'sections': sections, 'book': book})

@staff_member_required
def delete_page(request, id):
    db.delete_book(id)
    return redirect('/online_library')

def book_page(request, id):
    current_user = request.user

    sections = db.get_sections_list()
    book = db.find_one_book(id)
    all_comments = db.search_book_comments(book)
    favorites = db.is_in_favorite(current_user, id)
    user_rating = db.get_rating(current_user, id)
    book_rating = db.get_book_rating(id)

    p = Paginator(all_comments, 10)

    page = request.GET.get('page')
    try:
        comments = p.page(page)
    except PageNotAnInteger:
        comments = p.page(1)
    except EmptyPage:
        comments = p.page(p.num_pages)

    if request.method == 'POST':
        comment = request.POST['my_comment']
        db.add_comment(current_user, book, comment)
        return redirect('/online_library/book/'+id)

    return render(request, 'book_page.html', {'book': book, 'sections': sections, 'comments': comments,
                                              'current_user': current_user, 'favorites': favorites,
                                              'user_rating': user_rating, 'book_rating': book_rating})

def profile_page(request, id):
    user = User.objects.get(id=id)
    current_user = request.user
    sections = db.get_sections_list()
    all_comments = db.search_user_comments(user)
    comments = all_comments[0:5]
    all_favorites = db.search_favorites(user)
    favorites = all_favorites[0:5]

    return render(request, 'profile_page.html', {'sections': sections, 'user': user,
                                                 'current_user': current_user, 'comments': comments, 'favorites': favorites} )

def profile_comments_page(request, id):
    user = User.objects.get(id=id)
    current_user = request.user
    sections = db.get_sections_list()
    all_comments = db.search_user_comments(user)

    p = Paginator(all_comments, 5)

    page = request.GET.get('page')
    try:
        comments = p.page(page)
    except PageNotAnInteger:
        comments = p.page(1)
    except EmptyPage:
        comments = p.page(p.num_pages)

    return render(request, 'profile_comments_page.html', {'sections': sections, 'user': user,
                                                          'current_user': current_user, 'comments': comments} )

def profile_favorites_page(request, id):
    user = User.objects.get(id=id)
    current_user = request.user
    sections = db.get_sections_list()
    all_favorites = db.search_favorites(user)

    p = Paginator(all_favorites, 5)

    page = request.GET.get('page')
    try:
        favorites = p.page(page)
    except PageNotAnInteger:
        favorites = p.page(1)
    except EmptyPage:
        favorites = p.page(p.num_pages)

    return render(request, 'profile_favorites_page.html', {'sections': sections, 'user': user,
                                                           'current_user': current_user, 'favorites': favorites} )
@login_required()
def profile_edit_page(request, id):
    pass_error = ''
    current_user = request.user
    user = User.objects.get(id=id)

    if request.method == 'POST':
        name = request.POST['name']
        password = request.POST['password']
        new_password = request.POST['new_password']
        r_new_password = request.POST['r_new_password']
        if current_user == user or current_user.is_superuser:
            if user.check_password(password):
                if name != '' and name != user.username:
                    user.username = name
                if new_password != '' and new_password == r_new_password:
                    user.set_password(new_password)
                    password = new_password
            else:
                pass_error = 'Невірний пароль'
        user.save()
        update_session_auth_hash(request, user)
    return render(request, 'profile_edit_page.html', {'current_user': user, 'pass_error': pass_error})


@login_required
def like_page(request, id):
    current_user = request.user
    rating = db.get_rating(current_user, id)
    if rating:
        if rating['Rating'] < 1:
            db.update_rating(current_user, id, rating['Rating'] + 1)
    else:
        db.add_rating(current_user, id, 1)
    return redirect('/online_library/book/' + id)

@login_required
def dislike_page(request, id):
    current_user = request.user
    rating = db.get_rating(current_user, id)
    if rating:
        if rating['Rating'] > -1:
            db.update_rating(current_user, id, rating['Rating'] - 1)
    else:
        db.add_rating(current_user, id, -1)
    return redirect('/online_library/book/' + id)

@login_required
def delete_comment(request, id):
    comment = db.get_comment(id)
    if comment['User']['id'] == request.user.id or request.user.is_superuser:
        db.delete_comment(id)
    return redirect('/online_library/book/' + str(comment['Book_id']))

@staff_member_required
def stats_page(request):
    return render(request, 'stats_page.html')