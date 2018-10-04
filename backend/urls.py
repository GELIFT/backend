from django.conf.urls import url
from django.urls import include
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from rest_framework import routers
from rest_framework.authtoken import views as auth_views

from backend import views as backend_views

# REST framework URLs
router = routers.DefaultRouter()
router.register(r'user/device', FCMDeviceAuthorizedViewSet)
router.register(r'user/edit', backend_views.UserEdit, 'user_edit')
router.register(r'user/single', backend_views.UserView, 'single_user')
router.register(r'teams/my/start', backend_views.TeamLocationStart, 'start_timer')
router.register(r'teams/my/stop', backend_views.TeamLocationStop, 'stop_timer')

urlpatterns = [
    ### TODO: Remove /login/web in production
    url(r'^api-auth/user/login/web', include('rest_framework.urls')),
    url(r'^api/user/login/', auth_views.obtain_auth_token, name='api_login'),
    url(r'^api/user/logout/', backend_views.Logout.as_view(), name='api_logout'),
    url(r'^api/user/password_reset', backend_views.PasswordReset.as_view(), name='api_password_reset'),
    url(r'^api/user/$', backend_views.UserData.as_view(), name='api_user_data'),
    url(r'^api/', include(router.urls)),
    url(r'^api/challenges/$', backend_views.ChallengeView.as_view(), name='api_challenges'),
    url(r'^api/events/active/$', backend_views.ActiveEventView.as_view(), name='api_active_event'),
    url(r'^api/event/emergency/$', backend_views.EmergencyContactView.as_view(), name='api_edit_emergency_contact'),
    url(r'^api/teams/$', backend_views.TeamView.as_view(), name='api_teams'),
    url(r'^api/teams/my/$', backend_views.MyTeamView.as_view(), name='api_my_team'),
    url(r'^api/teams/my/route/$', backend_views.TeamRoute.as_view(), name='api_my_team_route'),
    url(r'^api/teams/my/location/$', backend_views.LocationView.as_view(), name='api_my_team_location'),
    url(r'^api/challenges/submit/$', backend_views.SubmitChallengeView.as_view(), name='api_challenge_submit'),
    url(r'^api/challenges/delete/$', backend_views.DeleteChallengeSubmissionView.as_view(),
        name='api_challenge_submission_delete'),
    url(r'^api/admin/challenges/$', backend_views.AdminChallengeView.as_view(), name='api_challenge_admin'),
    url(r'^api/admin/challenges/accept/$', backend_views.AcceptChallengeView.as_view(),
        name='api_challenge_admin_accept'),
    url(r'^api/admin/challenges/reject/$', backend_views.RejectChallengeView.as_view(),
        name='api_challenge_admin_reject'),
    url(r'^api/scoreboard/$', backend_views.Scoreboard.as_view(), name='api_scoreboard'),
]
