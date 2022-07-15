from contrib.views import get_items, start_page, items, count_items
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("get_items", get_items, name="get_items"),
    path("items", items, name='items'),
    path('items/count', count_items, name='count_item'),
    re_path(".*", start_page, name='start_page'),
]