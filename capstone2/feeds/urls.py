from django.urls import path

from feeds.views import FeedView

urlpatterns = [
    path("feeds/", FeedView.as_view(), name="feeds"),
]
