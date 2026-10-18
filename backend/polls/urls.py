from django.urls import path
from . import views

urlpatterns = [
    path("public/polls/", views.public_poll_list),
    path("public/polls/<int:poll_id>/vote/", views.vote),
    path("public/polls/<int:poll_id>/results/", views.public_results),
    path("host/polls/", views.host_polls),
    path("host/polls/<int:poll_id>/status/", views.change_status),
    path("host/polls/<int:poll_id>/results/", views.host_results),
]
