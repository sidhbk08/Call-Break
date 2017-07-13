from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from game import views as core_views


urlpatterns = [
    url(r'^$', core_views.home, name='home'),
    url(r'^highscore/$', core_views.highscore, name='highscore'),
    url(r'^rules/$', core_views.rules, name='rules'),
    url(r'^plus_minus/$', core_views.plus_minus, name='plus_minus'),
    url(r'^custom_team/$', core_views.custom_team, name='custom_team'),
    url(r'^login/$', core_views.custom_login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', core_views.custom_logout, {'next_page': 'login'}, name='logout'),
    url(r'^signup/$', core_views.signup, name='signup'),
    url(r'^admin/', admin.site.urls),
    url(r'^ajax/validate_username/$', core_views.validate_username, name='validate_username'),
    url(r'^waitreq/$', core_views.waitreq, name='waitreq'),
    url(r'^gooff/$', core_views.gooff, name='gooff'),
    url(r'^bhagu/$', core_views.bhagu, name='bhagu'),
    url(r'^myturn/$', core_views.myturn, name='myturn'),
    url(r'^call/$', core_views.call, name='call'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)