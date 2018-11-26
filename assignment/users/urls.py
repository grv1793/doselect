from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'^users/login', views.Login.as_view(),
        name='login'),
    url(r'^users/documents', views.DocumentList.as_view(),
        name='user-document'),
    url(r'^users/document/(?P<pk>[\w\-]+)/', views.DocumentDetail.as_view(),
        name='user-document-ded'),
]
