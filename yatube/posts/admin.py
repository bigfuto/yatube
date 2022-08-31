from django.contrib import admin
from .models import Post, Follow
from .models import Group, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    list_editable = ('group',)


admin.site.register(Group)
admin.site.register(Post, PostAdmin)
admin.site.register(Follow)
admin.site.register(Comment)
