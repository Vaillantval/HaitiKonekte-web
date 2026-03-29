from django.contrib import admin
from .models import SiteConfig, FAQCategorie, FAQItem, ContactMessage, SliderImage


@admin.register(SliderImage)
class SliderImageAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'ordre', 'is_active', 'created_at')
    list_editable = ('ordre', 'is_active')
    ordering      = ('ordre',)


class FAQItemInline(admin.TabularInline):
    model  = FAQItem
    extra  = 1
    fields = ('question', 'reponse', 'ordre', 'is_active')


@admin.register(FAQCategorie)
class FAQCategorieAdmin(admin.ModelAdmin):
    list_display = ('titre', 'ordre', 'is_active')
    inlines      = [FAQItemInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'email', 'sujet', 'statut', 'created_at')
    list_filter   = ('statut',)
    readonly_fields = ('nom', 'email', 'sujet', 'message', 'created_at')


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    pass
