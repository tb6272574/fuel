from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'fuel.views.index', name='index'),
    url(r'^home/$', 'fuel.views.home', name='home'),
    url(r'^game/$', 'fuel.views.game', name='game'),
    url(r'^action/addscale/(?P<scaleid>\d+)/(?P<amount>\d+)/$', 'fuel.views.addscale', name='addscale'),
    url(r'^login/$', 'fuel.views.login', name='login'),
    url(r'^logout/$', 'fuel.views.logout', name='logout'),
    url(r'^addrecord/', 'fuel.views.addrecord', name='addrecord'),
    url(r'^stats/$', 'fuel.views.stats', name='stats'),
    # url(r'^gsburn/', include('gsburn.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
