from typing import TYPE_CHECKING

from django.contrib import admin

from apps.catalog.models import Dish

if TYPE_CHECKING:
    BaseModelAdmin = admin.ModelAdmin[Dish]
else:
    BaseModelAdmin = admin.ModelAdmin


@admin.register(Dish)
class DishAdmin(BaseModelAdmin):
    list_display = ("name", "restaurant_id", "category", "price", "is_available", "created_at")
    list_filter = ("category", "is_available")
    search_fields = ("name", "description", "=restaurant_id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
