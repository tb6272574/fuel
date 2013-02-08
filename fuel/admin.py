from fuel.models import *
from django.contrib.sites.models import Site
from django.contrib.auth.models import User, Group 
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

class ProfileInline(admin.StackedInline):
    model = Profile

class UserProfileAdmin(UserAdmin):
    inlines = [ProfileInline, ]
    list_display = ('id', 'username', 'name', 'start_date', 'boost_day', 'status')

class AmountAdmin(admin.ModelAdmin):
    list_display = ('id', 'time', 'user', 'amount', 'atype', 'action')
    list_filter = ('user', 'atype')

class RecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'user', 'steps', 'calories', 'fuelscore', 'amount') 
    list_filter = ('user', 'date')

class ScaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'active', 'get_money', 'current_value', 'target', 'get_winner')
    list_filter = ('active',)

admin.site.unregister(User)
admin.site.register(FuelUser, UserProfileAdmin)
admin.site.register(Record, RecordAdmin)
admin.site.register(Amount, AmountAdmin)
#admin.site.register(FriendNode)
admin.site.register(Scale, ScaleAdmin)

admin.site.unregister(Group)
admin.site.unregister(Site)
