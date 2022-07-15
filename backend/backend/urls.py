from contrib.views import get_items, start_page, count_items, get_full_item
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("get_items", get_items, name="get_items"),
    path('<str:collection>/count', count_items, name='count_items'),
    path('item', get_full_item, name='get_full_item'),
    re_path(".*", start_page, name='start_page'),
]