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
from cesar.doc.views import *
from cesar.tsg.views import *
# The CesarLingo application
from cesar.lingo.views import *
# The brief application
from cesar.brief.views import *

# Import from CESAR as a whole
from cesar.settings import APP_PREFIX

# Other Django stuff
# EXTINCT from django.core import urlresolvers
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import RedirectView

admin.autodiscover()


# Set admin stie information
admin.site.site_header = "Corpus Editor for Syntactically Annotated Resources"
admin.site.site_title = "CESAR Admin"

pfx = APP_PREFIX

urlpatterns = [
    # Cesar lingo:
    url(r'^lingo$', cesar.lingo.views.home, name='lingo_home'),
    url(r'^lingo/about', cesar.lingo.views.about, name='lingo_about'),
    url(r'^lingo/experiment/list', ExperimentListView.as_view(), name='exp_list'),
    url(r'^lingo/experiment/details(?:/(?P<pk>\d+))?/$', ExperimentDetails.as_view(), name='exp_details'),
    url(r'^lingo/experiment/edit(?:/(?P<pk>\d+))?/$', ExperimentEdit.as_view(), name='exp_edit'),
    url(r'^lingo/experiment/do/(?P<pk>\d+)', ExperimentDo.as_view(), name='exp_do'),
    url(r'^lingo/experiment/download/(?P<pk>\d+)', ExperimentDownload.as_view(), name='exp_download'),
    url(r'^lingo/experiment/participant(?:/(?P<pk>\d+))?/$', ParticipantDetails.as_view(), name='participant'),

    url(r'^lingo/qdata/list', QdataListView.as_view(), name='qdata_list'),
    url(r'^lingo/qdata/add',  RedirectView.as_view(url='/'+APP_PREFIX+'admin/lingo/qdata/add'), name='qdata_add'),
    url(r'^lingo/qdata/view(?:/(?P<pk>\d+))?/$', QdataDetailsView.as_view(), name='qdata_details'),

    url(r'^crm/contacts', cesar.lingo.views.crm_contacts, name='crm_contacts'),

    # Cesar brief:
    url(r'^brief/$', cesar.brief.views.home, name='brief_home'),
    url(r'^brief/about', cesar.brief.views.about, name='brief_about'),
    url(r'^brief/update', cesar.brief.views.brief_load, name='brief_update'),
    url(r'^brief/project/list', ProjectListView.as_view(), name='project_list'),
    url(r'^brief/project/details(?:/(?P<pk>\d+))?/$', ProjectDetails.as_view(), name='project_details'),
    url(r'^brief/project/edit(?:/(?P<pk>\d+))?/$', ProjectEdit.as_view(), name='project_edit'),
    url(r'^brief/project/location/$', cesar.brief.views.set_section, name='project_location'),
    url(r'^brief/edit(?:/(?P<pk>\d+))?/$', BriefEdit.as_view(), name='brief_edit'),
    url(r'^brief/master(?:/(?P<pk>\d+))?/$', BriefMaster.as_view(), name='brief_master'),
    url(r'^brief/product/details(?:/(?P<pk>\d+))?/$', BriefProductDetails.as_view(), name='briefproduct_details'),
    url(r'^brief/product/edit(?:/(?P<pk>\d+))?/$', BriefProductEdit.as_view(), name='briefproduct_edit'),
    url(r'^brief/product/list', BriefProductList.as_view(), name='briefproduct_list'),

    # Cesar proper:
    url(r'^$', cesar.browser.views.home, name='home'),
    url(r'^contact$', cesar.browser.views.contact, name='contact'),
    url(r'^more$', cesar.browser.views.more, name='more'),
    url(r'^about', cesar.browser.views.about, name='about'),
    url(r'^short', cesar.browser.views.short, name='short'),
    url(r'^nlogin', cesar.browser.views.nlogin, name='nlogin'),

    url(r'^part/list', cesar.browser.views.PartListView.as_view(), name='part_list'),
    url(r'^part/view/(?P<pk>\d+)', PartDetailView.as_view(), name='part_view'),

    url(r'^text/info/(?P<pk>\d+)', TextDetailInfo.as_view(), name='text_info'),
    url(r'^text/list/$', cesar.browser.views.TextListView.as_view(), name='text_list'),
    url(r'^text/view/(?P<pk>\d+)', TextDetailView.as_view(), name='text_view'),
    url(r'^text/lines/(?P<pk>\d+)/$', SentenceListView.as_view(), name='text_lines'),
    url(r'^text/line/(?P<pk>\d+)/$', SentenceDetailView.as_view(), name='text_line'),
    url(r'^text/syntax/download/(?P<pk>\d+)/$', SentenceDetailView.as_view(), name='syntax_download'),

    url(r'^doc/concrete/$', cesar.doc.views.concrete_main, name='concrete_main'),
    url(r'^doc/concrete/list/$', ConcreteListView.as_view(), name='froglink_list'),
    url(r'^doc/concrete/details(?:/(?P<pk>\d+))?/$', ConcreteDetails.as_view(), name='froglink_details'),
    url(r'^doc/concrete/edit(?:/(?P<pk>\d+))?/$', ConcreteEdit.as_view(), name='froglink_edit'),
    url(r'^doc/concrete/download/(?P<pk>\d+)/$', ConcreteDownload.as_view(), name='concrete_download'),
    url(r'^doc/nexis/$', cesar.doc.views.nexis_main, name='nexis_main'),
    url(r'^doc/nexis/list/$', NexisListView.as_view(), name='nexisbatch_list'),
    url(r'^doc/nexis/details(?:/(?P<pk>\d+))?/$', NexisBatchDetails.as_view(), name='nexisbatch_details'),
    url(r'^doc/nexis/edit(?:/(?P<pk>\d+))?/$', NexisBatchEdit.as_view(), name='nexisbatch_edit'),
    url(r'^doc/nexis/download(?:/(?P<pk>\d+))?/$', NexisBatchDownload.as_view(), name='nexisbatch_download'),

    url(r'^api/import/concrete/$', cesar.doc.views.import_concrete, name='import_concrete'),
    url(r'^api/import/brysb/$', cesar.doc.views.import_brysbaert, name='import_brysb'),
    url(r'^api/import/nexis/$', cesar.doc.views.import_nexis, name='import_nexis'),

    url(r'^tsg/handle/sync', cesar.tsg.views.tsgsync, name='tsg_sync'),
    url(r'^tsg/handle/list', TsgHandleListView.as_view(), name='tsg_list'),
    url(r'^tsg/handle/details(?:/(?P<pk>\d+))?/$', TsgHandleDetails.as_view(), name='tsg_details'),
    url(r'^tsg/handle/edit(?:/(?P<pk>\d+))?/$', TsgHandleEdit.as_view(), name='tsg_edit'),

    url(r'^seek/wizard/(?P<object_id>\d+)/$', cesar.seeker.views.research_edit, name='seeker_edit'),
    url(r'^seek/wizard/new/$', cesar.seeker.views.research_edit, name='seeker_define'),
    url(r'^seek/wizard/import/$', cesar.seeker.views.import_json, name='import_file'),
    url(r'^seek/wizard/copy/(?P<object_id>\d+)/$', ResearchCopy.as_view(), name='seeker_copy'),
    url(r'^seek/wizard/delete/(?P<object_id>\d+)/$', ResearchDelete.as_view(), name='seeker_delete'),
    url(r'^seek/oview/(?P<object_id>\d+)/$', cesar.seeker.views.research_oview, name='seeker_oview'),

    url(r'^seek/simple/list/$', SimpleListView.as_view(), name='simple_list'),
    url(r'^seek/simple(?:/(?P<pk>\d+))?/$', cesar.seeker.views.research_simple, name='simple_details'),
    url(r'^seek/simple(?:/(?P<pk>\d+))?/$', cesar.seeker.views.research_simple, name='simple_edit'),
    url(r'^seek/simple/save/$', cesar.seeker.views.research_simple_save, name='simple_save'),
    url(r'^seek/simple/baresave/$', cesar.seeker.views.research_simple_baresave, name='simple_baresave'),

    url(r'^seek/result/kwic/(?P<pk>\d+)/$', KwicView.as_view(), name='kwic_result'),
    url(r'^seek/result/kwic/list/(?P<object_id>\d+)/$', KwicListView.as_view(), name='kwic_list'),
    url(r'^seek/result/quantor/(?P<object_id>\d+)/$', QuantorListView.as_view(), name='result_docs'),

    url(r'^seek/sgroup/list/$', ResGroupList.as_view(), name='sgroup_list'),
    url(r'^seek/sgroup(?:/(?P<object_id>\d+))?/$', ResGroupDetails.as_view(), name='sgroup'),

    url(r'^seek/result/list/$', ResultListView.as_view(), name='result_list'),
    url(r'^seek/result/(?P<pk>\d+)/$', ResultDetailView.as_view(), name='result_details'),
    url(r'^seek/result/docs/(?P<object_id>\d+)/$', ResultPart1.as_view(), name='result_part_1'),
    url(r'^seek/result/dochits/(?P<object_id>\d+)/$', ResultPart14.as_view(), name='result_part_14'),
    url(r'^seek/result/sents/(?P<object_id>\d+)/$', ResultPart2.as_view(), name='result_part_2'),
    url(r'^seek/result/filter/(?P<object_id>\d+)/$', ResultPart3.as_view(), name='result_part_3'),
    url(r'^seek/result/hit/(?P<object_id>\d+)/$', ResultPart4.as_view(), name='result_part_4'),
    url(r'^seek/result/tree/(?P<object_id>\d+)/$', ResultPart5.as_view(), name='result_part_5'),
    url(r'^seek/result/htable/(?P<object_id>\d+)/$', ResultPart6.as_view(), name='result_part_6'),
    url(r'^seek/result/download/(?P<object_id>\d+)/$', ResultDownload.as_view(), name='result_download'),
    url(r'^seek/result/hit/download/(?P<object_id>\d+)/$', ResultHitView.as_view(), name='hit_download'),
    url(r'^seek/result/delete/(?P<object_id>\d+)/$', ResultDelete.as_view(), name='result_delete'),

    url(r'^seek/list/$', SeekerListView.as_view(), name='seeker_list'),

    url(r'^function/list/$', FunctionListView.as_view(), name='function_list'),

    url(r'^sync/crpp$', cesar.browser.views.sync_crpp, name='crpp'),
    url(r'^sync/crpp/start/$', cesar.browser.views.sync_crpp_start, name='sync_start'),
    url(r'^sync/crpp/progress/$', cesar.browser.views.sync_crpp_progress, name='sync_progress'),

    url(r'^ajax/prepare(?:/(?P<object_id>\d+))?/$', ResearchPrepare.as_view(), name='search_prepare'),
    url(r'^ajax/watch(?:/(?P<object_id>\d+))?/$', ResearchWatch.as_view(), name='search_watch'),
    url(r'^ajax/start(?:/(?P<object_id>\d+))?/$', ResearchStart.as_view(), name='search_start'),
    url(r'^ajax/stop(?:/(?P<object_id>\d+))?/$', ResearchStop.as_view(), name='search_stop'),
    url(r'^ajax/download/crpx/(?P<object_id>\d+)/$', ResearchDownload.as_view(), name='search_download'),
    url(r'^ajax/download/json/(?P<object_id>\d+)/$', ResearchDownloadJson.as_view(), name='search_json'),
    url(r'^ajax/progress(?:/(?P<object_id>\d+))?/$', ResearchProgress.as_view(), name='search_progress'),
    url(r'^ajax/researchfield(?:/(?P<object_id>\d+))?/$', ResearchField.as_view(), name='research_field'),
    url(r'^ajax/researchpart1/$', ResearchPart1.as_view(), name='research_new'),
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
    url(r'^ajax/researchpart7(?:/(?P<object_id>\d+))?/$', ResearchPart7.as_view(), name='research_part_7'),
    url(r'^ajax/researchpart72(?:/(?P<object_id>\d+))?/$', ResearchPart72.as_view(), name='research_part_72'),
    url(r'^ajax/researchpart73(?:/(?P<object_id>\d+))?/$', ResearchPart73.as_view(), name='research_part_73'),
    url(r'^ajax/researchpart8(?:/(?P<object_id>\d+))?/$', ResearchPart8.as_view(), name='research_part_8'),
    url(r'^ajax/variable43(?:/(?P<object_id>\d+))?/$', Variable43.as_view(), name='variable43'),
    url(r'^ajax/condition63(?:/(?P<object_id>\d+))?/$', Condition63.as_view(), name='condition63'),
    url(r'^ajax/feature73(?:/(?P<object_id>\d+))?/$', Feature73.as_view(), name='feature73'),
    url(r'^ajax/variable43t(?:/(?P<object_id>\d+))?/$', Variable43t.as_view(), name='variable43t'),
    url(r'^ajax/condition63t(?:/(?P<object_id>\d+))?/$', Condition63t.as_view(), name='condition63t'),
    url(r'^ajax/feature73t(?:/(?P<object_id>\d+))?/$', Feature73t.as_view(), name='feature73t'),
    url(r'^ajax/function/download/(?P<object_id>\d+)/$', ResearchDownloadFunction.as_view(), name='function_download'),

    url(r'^definitions$', RedirectView.as_view(url='/'+pfx+'admin/'), name='definitions'),
    url(r'^signup/$', cesar.browser.views.signup, name='signup'),

    # For working with ModelWidgets from the select2 package https://django-select2.readthedocs.io
    url(r'^select2/', include('django_select2.urls')),

    url(r'^login/user/(?P<user_id>\w[\w\d_]+)$', cesar.browser.views.login_as_user, name='login_as'),

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
    url(r'^admin/', admin.site.urls, name='admin_base'),
]
