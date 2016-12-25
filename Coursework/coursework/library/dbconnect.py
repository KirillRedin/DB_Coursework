#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps, loads
from bson.code import Code
from django.core.files.storage import FileSystemStorage
from django.contrib import auth
import random
import redis
import datetime
# import os
# from django.contrib.auth.models import User

class DataBase(object):
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.libdb
        self.r = redis.Redis(host='localhost', port=6379)
        self.book_fs = FileSystemStorage(base_url='/media/books', location="media/books")
        self.img_fs = FileSystemStorage(base_url='/media/images', location="media/images")

    def add_book(self, title, author, section_name, description, book_file, image_file):
        bookname = self.book_fs.save(book_file.name, book_file)
        uploaded_book_url = self.book_fs.url(bookname)

        imagename = self.img_fs.save(image_file.name, image_file)
        uploaded_image_url = self.img_fs.url(imagename)

        section = self.db.sections.find_one({'Name' : {'$regex': '.*'+section_name+'.*', '$options': 'i'}})

        self.db.books.insert({'Title': title, 'Author': author, 'Description': description, 'Sections': section,
                              'Book_url': uploaded_book_url, 'Image_url': uploaded_image_url})
        self.r.delete(author)
        self.r.delete(section_name)
        return [title, author, uploaded_book_url, uploaded_image_url]

    def add_comment(self, user, book, comment):
        self.db.comments.insert({'User': {'id': user.id, 'Name': user.username }, 'Date': datetime.datetime.now().strftime("%d-%b-%Y"),
                                 'Time': datetime.datetime.now().strftime("%H:%M:%S"), 'Book_id': book['_id'], 'Text': comment})

    def add_to_favorite(self, user, book_id):
        book = self.find_one_book(book_id)
        self.db.favorites.insert({'User': {'id': user.id, 'Name': user.username }, 'Books': book})

    def add_rating(self, user, book_id, rating):
        self.db.ratings.insert({'User': {'id': user.id, 'Name': user.username}, 'Book_id': ObjectId(book_id), 'Rating': rating})

    def remove_from_favorite(self, user, book_id):
        self.db.favorites.delete_one({'User.id': user.id, 'Books._id': ObjectId(book_id)})

    def delete_book(self, book_id):
        book = self.find_one_book(book_id)
        self.db.favorites.delete_one({'Book_id': ObjectId(book_id)})
        self.db.books.delete_one({'_id': ObjectId(book_id)})
        self.db.comments.delete_one({'Book_id': ObjectId(book_id)})
        self.db.likes.ratings.delete_one({'Book_id': ObjectId(book_id)})
        self.r.delete(book['Author'])
        self.r.delete(book['Sections']['Name'])

    def delete_comment(self, comment_id):
        self.db.comments.delete_one({'_id': ObjectId(comment_id)})

    def edit_book(self, book, title, author, section_name, description, book_file, image_file):
        if book_file != 'none':
            bookname = self.book_fs.save(book_file.name, book_file)
            uploaded_book_url = self.book_fs.url(bookname)
        else:
            uploaded_book_url = book['Book_url']

        if image_file != 'none':
            imagename = self.img_fs.save(image_file.name, image_file)
            uploaded_image_url = self.img_fs.url(imagename)
        else:
            uploaded_image_url = book['Image_url']

        section = self.db.sections.find_one({'Name' : {'$regex': '.*'+section_name+'.*', '$options': 'i'}})

        edited_book = {'_id': book['_id'], 'Title' : title, 'Author': author, 'Description': description,
                       'Book_url': uploaded_book_url, 'Image_url': uploaded_image_url, "Sections": section}
        self.r.delete(book['Author'])
        self.r.delete(book['Sections']['Name'])
        self.db.books.update_one({'_id': book['_id']}, {'$set': edited_book})
        self.db.favorites.update({'Books._id': book['_id']}, {'$set': {'Books': edited_book} })
        self.r.delete(author)
        self.r.delete(section_name)
        return [title, author, uploaded_book_url, uploaded_image_url]

    def update_rating(self, user, book_id, rating):
        self.db.ratings.update_one({'Book_id': ObjectId(book_id), 'User.id': user.id}, {'$set': {'Rating': rating}})

    def find_one_book(self, id):
        book = self.db.books.find_one({'_id': ObjectId(id)})
        return book

    def get_books_list(self):
        books = list(self.db.books.find())
        return books

    def get_sections_list(self):
        sections = list(self.db.sections.find())
        return sections

    def get_rating(self, user, book_id):
        rating = self.db.ratings.find_one({'User.id': user.id, 'Book_id': ObjectId(book_id)})
        return rating

    def get_book_rating(self, book_id):
        ratings = self.db.ratings.aggregate([{'$group': {'_id': '$Book_id', 'Sum': {'$sum': '$Rating'}}}])
        for rating in ratings:
            if rating['_id'] == ObjectId(book_id):
                return rating['Sum']
        return 0

    def get_comment(self, comment_id):
        comment = self.db.comments.find_one({'_id': ObjectId(comment_id)})
        return comment

    def search_favorites(self, user):
        favorites = list(self.db.favorites.find({'User.id': user.id}))
        return favorites

    def search_book_comments(self, book):
        sorted_comments = list(self.db.comments.aggregate(
            [{'$sort': {'Date': -1, 'Time': -1}}, {'$match': {'Book_id': book['_id']}}]))
        return sorted_comments

    def search_user_comments(self, user):
        sorted_comments = list(self.db.comments.aggregate(
            [{'$sort': {'Date': -1, 'Time': -1}}, {'$match': {'User.id': user.id}}]))
        return sorted_comments

    def search_sections(self, section_name):
        sections = list(self.db.sections.find({'Name' : {'$regex': '.*'+section_name+'.*', '$options': 'i'}}))
        return sections

    def search_books(self, title_phrase, author_phrase, section_name):
        sections = self.search_sections(section_name)
        books = list(self.db.books.find({'Title' : {'$regex': '.*'+title_phrase+'.*', '$options': 'i'},
                                                    'Author': {'$regex': '.*' + author_phrase + '.*', '$options': 'i'},
                                                      'Sections.Name': {'$regex': '.*' + section_name + '.*', '$options': 'i'}}))
        return books

    def search_by_author(self, author_phrase):
        books = list(self.db.books.find({'Author': {'$regex': '.*' + author_phrase + '.*', '$options': 'i'}}))
        return books

    def search_by_title(self, title_phrase):
        books = list(self.db.books.find({'Title': {'$regex': '.*' + title_phrase + '.*', '$options': 'i'}}))
        return books

    def search_by_section(self, section_name):
        if self.chk_cache(section_name) == 'using cache':
            books = loads(self.r.get(section_name))
        else:
            books = list(self.db.books.find({'Sections.Name': section_name}))
            self.r.set(section_name, dumps(books))
        return books

    def author_search(self, author):
        if self.chk_cache(author) == 'using cache':
            books = loads(self.r.get(author))
        else:
            books = list(self.db.books.find({'Author': author}))
            self.r.set(author, dumps(books))
        return books

    def is_in_favorite(self, user, book_id):
        favorites = list(self.db.favorites.find({'User.id': user.id, 'Books._id': ObjectId(book_id)}))
        return favorites

    def chk_cache(self, key):
        if self.r.exists(key) != 0:
            return 'using cache'
        return 'without cache'

    def top_genres(self):
        genres = self.db.books.aggregate([{'$group': {'_id': '$Sections.Name', 'Count': {'$sum': 1}}},
                                          {'$sort': {'Count': -1}}, {'$limit': 3}])
        return list(genres)

    def top_books(self):
        ratings = list(self.db.ratings.aggregate([{'$group': {'_id': '$Book_id', 'Rating': {'$sum': '$Rating'}}},
                                                  {'$sort': {'Rating': -1}}, {'$limit':3}]))
        for rating in ratings:
            books = list

db = DataBase()

# top = db.top_genres()
# print top
    # def get_img_urls(self):
    #     img_urls = [Url for Url in self.db.image_urls.find()]
    #     return img_urls
    #
    # def get_book_urls(self):
    #     book_urls = [Url for Url in self.db.book_urls.find()]
    #     return book_urls
    #
    # def get_titles(self):
    #     titles = [Title for Title in self.db.titles.find()]
    #     return titles
    #
    # def get_authors(self):
    #     authors = [Author for Author in self.db.authors.find()]
    #     return authors
    #
    # def get_descriptions(self):
    #     descriptions = [Description for Description in self.db.descriptions.find()]
    #     return descriptions
    #
    #
    # def randomize(self):
    #     for x in xrange(1, 20000):
    #         Title = random.choice(self.get_titles())
    #         Author = random.choice(self.get_authors())
    #         Description = random.choice(self.get_descriptions())
    #         Book_url = random.choice(self.get_book_urls())
    #         Image_url = random.choice(self.get_img_urls())
    #         Section = random.choice(self.get_sections_list())
    #
    #         book = {'Title': Title['Title'], 'Author': Author['Name'], 'Description': Description['Description'],
    #                 'Book_url': Book_url['url'], 'Image_url': Image_url['Image_url'], 'Sections': Section}
    #         self.db.books.insert(book)
    #         print x
    #
    # def get_comms(self):
    #     comms = list(self.db.comms.find())
    #     return comms
    #
    # def randomize2(self):
    #     books = self.get_books_list()
    #     users = User.objects.all()
    #     comms = self.get_comms()
    #         # i = 0
    #         # for book in books:
    #         #     for user in users:
    #         #         self.add_rating(user, book['_id'], random.randint(-1, 1))
    #         #     i = i + 1
    #         #     print i
    #
    #     for x in xrange(1, 100):
    #         book = random.choice(books)
    #         for user in users:
    #             comment = random.choice(comms)
    #             self.add_comment(user, book, comment['Comment'])
    #             self.add_to_favorite(user, book['_id'])
    #         print x
    #

# db = DataBase()
# db.randomize2()
# db.randomize()
# print db.get_book_rating('5857f7bc7aab1417d44fa094')