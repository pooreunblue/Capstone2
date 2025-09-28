from django.urls import path

from feeds.views import FeedView

urlpatterns = [
    path("", FeedView.as_view(), name="feeds"),
]
