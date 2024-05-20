from django.urls import path
from .views import *

urlpatterns = [
        path('teacher/users/create/', TeacherUserCreateView.as_view(), name='teacher_user_create'),
        path('fetch/teacher/detail/<int:pk>/', FetchTeacherDetailView.as_view(), name='fetch_student_detail'),
        path('teacher/list/', TeacherListView.as_view(), name='student_list'),
        path('teacher/delete/<int:pk>/', TeacherDeleteView.as_view(), name='teacher_delete'),
        path('teacher/update-profile/<int:pk>/', TeacherUpdateProfileView.as_view(), name='update_teacher_profile'),

        #Teacher schedule API'S
        path('schedule/create/', TeacherScheduleCreateView.as_view(), name='schedule_create'),
        path('schedule/detail/<int:pk>/', TeacherScheduleDetailView.as_view(), name='schedule_detail'),
        path('schedule/list/', TeacherScheduleListView.as_view(), name='schedule_list'),
        path('schedule/delete/<int:pk>/', TeacherScheduleDeleteView.as_view(), name='schedule_delete'),
        path('schedule/update/<int:pk>/', TeacherScheduleUpdateView.as_view(), name='schedule_update'),
        path('schedule/renew/<int:pk>/', TeacherScheduleRenewView.as_view(), name='schedule_renew'),
        path('schedule/teacher/list/', TeachersListView.as_view(), name='teachers_list'),
        path('schedule/curriculum/list/', TeachersCurriculumListView.as_view(), name='schedule_curriculum_list'),
        path('schedule/class/list/', TeachersClassListView.as_view(), name='schedule_class_list'),
        path('schedule/section/list/', TeachersSectionListView.as_view(), name='schedule_section_list'),
        path('schedule/subject/list/', TeachersSubjectListView.as_view(), name='schedule_subject_list'),

        #Teacher attendence API's
        path('user/login/', UserLoginView.as_view(), name='user_login'),
        path('attendance/create/', TeacherAttendanceCreateView.as_view(), name='attendance_create'),
        path('attendance/detail/<int:pk>/', FetchAttendanceDetailView.as_view(), name='fetch_attendance_detail'),
        path('attendance/list/',  FetchAttendanceListView.as_view(), name='fetch_attendance_list'),
        path('attendance/filter/list/', AttedanceFilterListView.as_view(), name='attendance_filter_list'),

        # Curriculum API'S
        path('section/list/', SectionListView.as_view(), name='class_list'),
        path('subjects/list/', SubjectListView.as_view(), name='subject_list'),

        # Mobile Chat API'S
        path('availability/create/', AvailabilityCreateView.as_view(), name='availability_create'),
        path('availability/update/', AvailabilityUpdateView.as_view(), name='availability_update'),
        path('availability/get/', AvailabilityGetView.as_view(), name='availability_get'),
        path('chat/request/', StudentChatRequestView.as_view(), name='chat_request'),
        path('chat/request/accept/<int:pk>/', StudentChatRequestAcceptView.as_view(), name='chat_request_accept'),
        path('chat/join/<int:pk>/', StudentChatRequestJoinView.as_view(), name='chat_join'),
        path('chat/history/', StudentChatHistoryView.as_view(), name='chat_history'),
]