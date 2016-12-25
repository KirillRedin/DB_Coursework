from django.conf.urls import url
import views

urlpatterns = [
    url(r'^$', views.mainpage),
    url(r'^(?P<author_name>[\w\s]+)/$', views.author_page),
    url(r'^admin/add_book/$', views.add_page),
    url(r'^admin/stats/$', views.stats_page),
    url(r'^admin/edit_book/(?P<id>[\w]+)/$', views.edit_page),
    url(r'^admin/delete_book/(?P<id>[\w]+)/$', views.delete_page),
    url(r'^admin/change_active/(?P<id>[\w]+)/$', views.change_active),
    url(r'^book/(?P<id>[\w]+)/$', views.book_page),
    url(r'^profile/(?P<id>[\w]+)/$', views.profile_page),
    url(r'^profile/comments/(?P<id>[\w]+)/$', views.profile_comments_page),
    url(r'^profile/favorites/(?P<id>[\w]+)/$', views.profile_favorites_page),
    url(r'^profile/edit/(?P<id>[\w]+)/$', views.profile_edit_page),
    url(r'^add_favorite/(?P<id>[\w]+)/$', views.add_favorite_page),
    url(r'^like/(?P<id>[\w]+)/$', views.like_page),
    url(r'^dislike/(?P<id>[\w]+)/$', views.dislike_page),
    url(r'^delete_comment/(?P<id>[\w]+)/$', views.delete_comment),
]