"""
Definition of urls for cesar.
"""

from datetime import datetime
from django.contrib.auth.decorators import login_required, permission_required
# Uncomment the next lines to enable the admin:
from django.conf.urls import include, url
from django.contrib import admin
import django.contrib.auth.views

# Import from the app 'browser'
import cesar.browser.views
from cesar.browser.views import *
from cesar.browser.forms import *
from cesar.seeker.views import *

# Import from CESAR as a whole
from cesar.settings import APP_PREFIX

# Other Django stuff
from django.core import urlresolvers
from django.shortcuts import redirect
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.base import RedirectView

admin.autodiscover()


# Set admin stie information
admin.site.site_header = "Corpus Editor for Syntactically Annotated Resources"
admin.site.site_title = "CESAR Admin"

pfx = APP_PREFIX

urlpatterns = [
    # Examples:
    url(r'^$', cesar.browser.views.home, name='home'),
    url(r'^contact$', cesar.browser.views.contact, name='contact'),
    url(r'^more$', cesar.browser.views.more, name='more'),
    url(r'^about', cesar.browser.views.about, name='about'),
    url(r'^nlogin', cesar.browser.views.nlogin, name='nlogin'),
    url(r'^part/list', cesar.browser.views.PartListView.as_view(), name='part_list'),
    url(r'^part/view/(?P<pk>\d+)', PartDetailView.as_view(), name='part_view'),
    url(r'^text/list/$', cesar.browser.views.TextListView.as_view(), name='text_list'),
    url(r'^text/view/(?P<pk>\d+)', TextDetailView.as_view(), name='text_view'),
    url(r'^text/lines/(?P<pk>\d+)/$', SentenceListView.as_view(), name='text_lines'),
    url(r'^text/line/(?P<pk>\d+)/$', SentenceDetailView.as_view(), name='text_line'),
    url(r'^seek/wizard/$', cesar.seeker.views.research_edit, name='seeker_define'),
    url(r'^seek/wizard/(?P<object_id>\d+)/$', cesar.seeker.views.research_edit, name='seeker_edit'),
    url(r'^seek/oview/(?P<object_id>\d+)/$', cesar.seeker.views.research_oview, name='seeker_oview'),
    url(r'^seek/wizard/copy/(?P<object_id>\d+)/$', ResearchCopy.as_view(), name='seeker_copy'),
    url(r'^seek/wizard/delete/(?P<object_id>\d+)/$', ResearchDelete.as_view(), name='seeker_delete'),
    url(r'^seek/result/list/$', BasketListView.as_view(), name='result_list'),
    url(r'^seek/result/kwic/(?P<pk>\d+)/$', KwicView.as_view(), name='kwic_result'),
    url(r'^seek/result/kwic/list/(?P<pk>\d+)/$', KwicListView.as_view(), name='kwic_list'),
    url(r'^seek/result/(?P<object_id>\d+)/$', QuantorListView.as_view(), name='search_result'),
    url(r'^seek/list/$', SeekerListView.as_view(), name='seeker_list'),
    url(r'^function/list/$', FunctionListView.as_view(), name='function_list'),
    url(r'^sync/crpp$', cesar.browser.views.sync_crpp, name='crpp'),
    url(r'^sync/crpp/start/$', cesar.browser.views.sync_crpp_start, name='sync_start'),
    url(r'^sync/crpp/progress/$', cesar.browser.views.sync_crpp_progress, name='sync_progress'),
    url(r'^ajax/start(?:/(?P<object_id>\d+))?/$', ResearchStart.as_view(), name='search_start'),
    url(r'^ajax/stop(?:/(?P<object_id>\d+))?/$', ResearchStop.as_view(), name='search_stop'),
    url(r'^ajax/progress(?:/(?P<object_id>\d+))?/$', ResearchProgress.as_view(), name='search_progress'),
    url(r'^ajax/researchpart1(?:/(?P<object_id>\d+))?/$', ResearchPart1.as_view(), name='research_part_1'),
    url(r'^ajax/researchpart2(?:/(?P<object_id>\d+))?/$', ResearchPart2.as_view(), name='research_part_2'),
    url(r'^ajax/researchpart3(?:/(?P<object_id>\d+))?/$', ResearchPart3.as_view(), name='research_part_3'),
    url(r'^ajax/researchpart4(?:/(?P<object_id>\d+))?/$', ResearchPart4.as_view(), name='research_part_4'),
    url(r'^ajax/researchpart42(?:/(?P<object_id>\d+))?/$', ResearchPart42.as_view(), name='research_part_42'),
    url(r'^ajax/researchpart43(?:/(?P<object_id>\d+))?/$', ResearchPart43.as_view(), name='research_part_43'),
    url(r'^ajax/researchpart44(?:/(?P<object_id>\d+))?/$', ResearchPart44.as_view(), name='research_part_44'),
    url(r'^ajax/researchpart6(?:/(?P<object_id>\d+))?/$', ResearchPart6.as_view(), name='research_part_6'),
    url(r'^ajax/researchpart62(?:/(?P<object_id>\d+))?/$', ResearchPart62.as_view(), name='research_part_62'),
    url(r'^ajax/researchpart63(?:/(?P<object_id>\d+))?/$', ResearchPart63.as_view(), name='research_part_63'),
    url(r'^ajax/variable43(?:/(?P<object_id>\d+))?/$', Variable43.as_view(), name='variable43'),
    url(r'^ajax/researchpart43(?:/(?P<object_id>\d+))?/$', ResearchPart43.as_view(), name='research_part_43'),
    url(r'^definitions$', RedirectView.as_view(url='/'+pfx+'admin/'), name='definitions'),
    url(r'^signup/$', cesar.browser.views.signup, name='signup'),

    url(r'^login/$',
        django.contrib.auth.views.login,
        {
            'template_name': 'login.html',
            'authentication_form': cesar.browser.forms.BootstrapAuthenticationForm,
            'extra_context':
            {
                'title': 'Log in',
                'year': datetime.now().year,
            }
        },
        name='login'),
    url(r'^logout$',
        django.contrib.auth.views.logout,
        {
            'next_page': reverse_lazy('home'),
        },
        name='logout'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls), name='admin_base'),
]
