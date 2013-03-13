from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # close all the things!
    url(r'^faq/$', 'fuel.views.closed'),   
    url(r'^home/$', 'fuel.views.closed'),   
    url(r'^history/$', 'fuel.views.closed'),   
    url(r'^game/$', 'fuel.views.closed'),   
    url(r'^stats/$', 'fuel.views.closed'),   
    url(r'^videos/$', 'fuel.views.closed'),   
    url(r'^videos/submit/$', 'fuel.views.closed'),   
    url(r'^settings/$', 'fuel.views.closed'),   
    url(r'^survey-submit/$', 'fuel.views.closed'),   
    
    # old ones
    url(r'^$', 'fuel.views.index', name='index'),
    url(r'^faq/$', 'fuel.views.faq', name='faq'),
    url(r'^home/$', 'fuel.views.home', name='home'),
    url(r'^history/$', 'fuel.views.history', name='history'),
    url(r'^game/$', 'fuel.views.game', name='game'),
    url(r'^login/$', 'fuel.views.login', name='login'),
    url(r'^logout/$', 'fuel.views.logout', name='logout'),
    url(r'^stats/$', 'fuel.views.stats', name='stats'),
    url(r'^videos/$', 'fuel.views.videos', name='videos'),
    url(r'^videos/submit/$', 'fuel.views.videos_submit', name='videos_submit'),
    url(r'^settings/$', 'fuel.views.settings', name='settings'),
    url(r'^dashboard/$', 'fuel.views.dashboard', name='dashboard'),
    url(r'^survey-submit/$', 'fuel.views.survey_submit', name='survey_submit'),
    # actions
    url(r'^action/addrecord/', 'fuel.views.addrecord', name='addrecord'),
    url(r'^action/addscale/(?P<scaleid>\d+)/(?P<amount>\d+)/$', 'fuel.views.addscale', name='addscale'),
    # url(r'^gsburn/', include('gsburn.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
