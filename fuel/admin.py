from fuel.models import *
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

class ProfileInline(admin.StackedInline):
    model = Profile

class UserProfileAdmin(UserAdmin):
    inlines = [ProfileInline, ]
    list_display = ('username', 'name', 'start_date', 'boost_day', 'status')

admin.site.unregister(User)
admin.site.register(FuelUser, UserProfileAdmin)
admin.site.register(Record)
admin.site.register(Amount)
admin.site.register(FriendNode)
admin.site.register(Scale)
