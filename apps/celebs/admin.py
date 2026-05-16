from django.contrib import admin

from .models import Category, Family, Type, Celeb, Review, Comment, Country, CelebPhoto


class TypeInline(admin.TabularInline):
    model = Type
    extra = 1
    fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class FamilyInline(admin.TabularInline):
    model = Family
    extra = 1
    fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'family_count')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FamilyInline]

    def family_count(self, obj):
        return obj.families.count()
    family_count.short_description = 'Families'


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'type_count')
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TypeInline]

    def type_count(self, obj):
        return obj.types.count()
    type_count.short_description = 'Types'


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('flag', 'name', 'code')
    search_fields = ('name', 'code')


@admin.register(Celeb)
class CelebAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'type', 'rating', 'published')
    list_filter = ('published', 'nationality', 'type__family__category', 'type__family', 'type')
    list_editable = ('published',)
    search_fields = ('name', 'street_name')
    prepopulated_fields = {'slug': ('name',)}

    class PhotoInline(admin.TabularInline):
        model = CelebPhoto
        extra = 1
        fields = ('image', 'caption')

    inlines = [PhotoInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'celeb', 'rating', 'created_at')
    list_filter = ('rating', 'celeb')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'celeb', 'created_at')
    list_filter = ('celeb',)
