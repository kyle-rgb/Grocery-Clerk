from contrib.views import get_items, start_page
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("get_items", get_items, name="get_items"),
    re_path(".*", start_page, name='start_page'),
]