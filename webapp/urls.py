from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import path

import webapp.views as views

# SetPasswordForm.errors.__str__()
urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),

    path(r'user/password/reset/',
         auth_views.PasswordResetView.as_view(template_name='webapp/authentication/password_reset.html'),
         name='password_reset'),
    url(r'^user/password/reset/done/$',
        auth_views.PasswordResetDoneView.as_view(template_name='webapp/authentication/password_reset_done.html'),
        name='password_reset_done'),
    path('user/password/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='webapp/authentication/password_reset_confirm.html'),
         name='password_reset_confirm'),
    url(r'^user/password/reset/complete', auth_views.PasswordResetCompleteView.as_view(
        template_name='webapp/authentication/password_reset_complete.html'), name='password_reset_complete'),

    url(r'^admin/dashboard/$', views.admin_dashboard, name='admin_dashboard'),
    url(r'^admin/user/$', views.user, name='user_list'),
    url(r'^admin/user/add/$', views.add_user, name='add_user'),
    url(r'^admin/user/remove/$', views.delete_user, name='delete_user'),
    path(r'admin/user/edit/<user_id>/', views.edit_user, name='edit_user'),

    url(r'^event_list/$', views.event_list, name='event_list'),
    path(r'event/<event_id>/', views.event, name='event_detail'),
    url(r'^admin/event/add/$', views.add_event, name='new_event'),
    path(r'admin/event/edit/<event_id>/', views.edit_event, name='edit_event'),
    path(r'admin/event/edit/<event_id>/location/', views.edit_event_location, name='edit_event_location'),
    path(r'admin/event/delete/<event_id>/', views.delete_event, name='delete_event'),
    path(r'admin/event/edit/<event_id>/active', views.mark_event_active, name='make_event_active'),
    path(r'admin/event/edit/<event_id>/inactive', views.mark_event_inactive, name='make_event_inactive'),
    path(r'admin/event/edit/team/delete', views.delete_team, name='delete_team'),
    path(r'admin/event/edit/<event_id>/teams/', views.edit_teams, name='edit_teams'),
    url(r'^admin/event/city/edit/$', views.edit_event_city_name, name='edit_city_name_event'),
    url(r'^admin/event/edit/teams/add/$', views.add_team, name='add_team'),
    url(r'^admin/event/edit/teams/members/add/$', views.add_member, name='add_member'),
    url(r'^admin/event/edit/teams/members/remove/$', views.remove_member, name='remove_member'),
    url(r'^admin/event/edit/teams/members/move/$', views.move_member, name='move_member'),
    url(r'^admin/event/edit/subdestination/add/$', views.add_sublocation, name='add_sublocation'),
    path(r'admin/event/edit/<event_id>/subdestinations/', views.edit_sublocation, name='edit_sublocation'),
    path(r'admin/event/edit/subdestination/delete/', views.delete_event_sublocation, name='delete_sublocation'),
    url(r'^admin/event/edit/subdestination/coordinates/$', views.edit_sublocation_coordinates,
        name='coordinates_sublocation'),
    url(r'^admin/event/edit/subdestination/city/$', views.edit_sublocation_city, name='city_sublocation'),
    url(r'^admin/event/edit/subdestination/order/$', views.edit_sublocation_order, name='order_sublocation'),

    url(r'^admin/administrators/$', views.administrators, name='edit_admins'),
    url(r'^admin/administrators/add/$', views.add_administrator, name='add_administrator'),
    url(r'^admin/administrators/remove/$', views.remove_administrator, name='remove_administrator'),

    url(r'^admin/location/add', views.add_location, name='add_location'),

    path(r'event/<event_id>/challenges', views.challenges, name='challenge'),
    path(r'challenges/<challenge_id>', views.challenge_detail, name='challenge_detail'),
    path(r'admin/event/<event_id>/challenges/add', views.add_challenge, name='add_challenge'),
    url(r'^admin/challenges/delete/$', views.delete_challenge, name='delete_challenge'),
    path(r'admin/challenges/edit/<challenge_id>/', views.edit_challenge, name='edit_challenge'),

    url(r'^admin/team/add/$', views.add_team, name='add_team'),
    url(r'^admin/team/disqualify/$', views.disqualify_team, name='disqualify_team'),
    url(r'^admin/team/disqualify/revert/$', views.undisqualify_team, name='undisqualify_team'),

    path(r'admin/event/<event_id>/winners/', views.event_winners, name='set_winners'),
    path(r'admin/event/<event_id>/winners/edit/', views.edit_event_winners, name='edit_winners'),
    path(r'admin/event/<event_id>/winners/remove/', views.delete_event_winners, name='delete_winner'),

]
