from django.conf.urls import patterns, url

from monopoly import views

urlpatterns = patterns('',
	url(r'^$', views.index, name='index'),
	url(r'^cors/$', views.cors, name='cors'),
)
