from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'fuel.views.index', name='index'),
    url(r'^faq/$', 'fuel.views.faq', name='faq'),
    url(r'^home/$', 'fuel.views.home', name='home'),
    url(r'^history/$', 'fuel.views.history', name='history'),
    url(r'^game/$', 'fuel.views.game', name='game'),
    url(r'^login/$', 'fuel.views.login', name='login'),
    url(r'^logout/$', 'fuel.views.logout', name='logout'),
    url(r'^stats/$', 'fuel.views.stats', name='stats'),
    url(r'^settings/$', 'fuel.views.settings', name='settings'),

    # actions
    url(r'^action/addrecord/', 'fuel.views.addrecord', name='addrecord'),
    url(r'^action/addscale/(?P<scaleid>\d+)/(?P<amount>\d+)/$', 'fuel.views.addscale', name='addscale'),
    # url(r'^gsburn/', include('gsburn.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
