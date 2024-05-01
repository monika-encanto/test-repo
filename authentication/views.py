import calendar
import datetime
import json

from django.db import IntegrityError
from django.utils import timezone
from pytz import timezone as pytz_timezone
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.dateparse import parse_date

from authentication.models import User, AddressDetails, ErrorLogging, Certificate, StaffUser, StaffAttendence, \
    TeacherUser, StudentUser, TeachersSchedule, DayReview, TeacherAttendence, Notification, TimeTable, EventsCalender
from authentication.permissions import IsSuperAdminUser, IsAdminUser, IsManagementUser, IsPayRollManagementUser, \
    IsBoardingUser, IsInSameSchool, IsTeacherUser
from authentication.serializers import UserSignupSerializer, UsersListSerializer, UpdateProfileSerializer, \
    UserLoginSerializer, NonTeachingStaffSerializers, NonTeachingStaffListSerializers, \
    NonTeachingStaffDetailSerializers, NonTeachingStaffProfileSerializers, StaffAttendanceSerializer, \
    StaffAttendanceDetailSerializer, StaffAttendanceListSerializer, LogoutSerializer, EventSerializer, EventsCalendarSerializer
from constants import UserLoginMessage, UserResponseMessage, AttendenceMarkedMessage, ScheduleMessage, \
    CurriculumMessage, DayReviewMessage, NotificationMessage, AnnouncementMessage, TimeTableMessage, ReportCardMesssage, \
    ZoomLinkMessage, StudyMaterialMessage, EventsMessages
from curriculum.models import Curriculum
from pagination import CustomPagination
from student.models import ExmaReportCard, ZoomLink, StudentMaterial
from student.serializers import StudentDetailSerializer, StudentUserProfileSerializer
from superadmin.models import Announcement
from teacher.serializers import TeacherDetailSerializer, TeacherProfileSerializer, TeacherUserProfileSerializer, \
    TeacherUserScheduleSerializer, CurriculumTeacherListerializer, DayReviewSerializer, DayReviewDetailSerializer, \
    TeacherUserAttendanceListSerializer, NotificationSerializer, NotificationListSerializer, \
    AnnouncementCreateSerializer, CreateTimeTableSerializer, AnnouncementListSerializer, TimeTableListSerializer, \
    TimeTableDetailSerializer, TimeTableUpdateSerializer, ExamReportCreateSerializer, ExamReportListSerializer, \
    ExamReportCardViewSerializer, ExamReportcardUpdateSerializer, ZoomLinkCreateSerializer, ZoomLinkListSerializer, \
    StudyMaterialUploadSerializer, StudyMaterialListSerializer, StudyMaterialDetailSerializer
from utils import create_response_data, create_response_list_data, get_staff_total_attendance, \
    get_staff_monthly_attendance, get_staff_total_absent, get_staff_monthly_absent


class UserCreateView(APIView):
    permission_classes = [IsSuperAdminUser | IsAdminUser]
    """
    This class is used to create the user's for authentication.
    """

    def post(self, request):
        try:
            serializer = UserSignupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            name = serializer.validated_data['name']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            phone = serializer.validated_data['phone']
            user_type = serializer.validated_data['user_type']

            address_line_1 = serializer.validated_data['address_line_1']
            address_line_2 = serializer.validated_data['address_line_2']
            city = serializer.validated_data['city']
            state = serializer.validated_data['state']
            country = serializer.validated_data['country']
            pincode = serializer.validated_data['pincode']

            if user_type == 'admin':
                user = User.objects.create_admin_user(
                    name=name, email=email, password=password, phone=phone, user_type=user_type
                )
            elif user_type == 'management' or user_type == 'payrollmanagement' or user_type == 'boarding':
                user = User.objects.create_user(
                    name=name, email=email, password=password, phone=phone, user_type=user_type
                )
            else:
                raise ValidationError(
                    "Invalid user_type. Expected 'admin', 'management', 'payrollmanagement', 'boarding'.")
            user_address = AddressDetails.objects.create(
                user=user, address_line_1=address_line_1, address_line_2=address_line_2, city=city, state=state,
                country=country, pincode=pincode
            )
            response_data = {
                'user_id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': str(user.phone),
                'is_email_verified': user.is_email_verified,
                'user_type': user.user_type
            }
            response = create_response_data(
                status=status.HTTP_201_CREATED,
                message=UserLoginMessage.SIGNUP_SUCCESSFUL,
                data=response_data
            )
            return Response(response, status=status.HTTP_201_CREATED)

        except KeyError as e:
            return Response(f"Missing key in request data: {e}", status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response("User already exist", status=status.HTTP_400_BAD_REQUEST)


class FetchUserDetailView(APIView):
    permission_classes = [IsAdminUser | IsManagementUser | IsPayRollManagementUser | IsBoardingUser]
    """
    This class is used to fetch the detail of the user.
    """

    def get(self, request, pk):
        try:
            data = User.objects.get(id=pk)
            serializer = UsersListSerializer(data)
            resposne = create_response_data(
                status=status.HTTP_200_OK,
                message=UserResponseMessage.USER_DETAIL_MESSAGE,
                data=serializer.data,
            )
            return Response(resposne, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

#IsAdminUser
class UsersList(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    """
    This class is used to fetch the list of the user's.
    """

    def get(self, request):
        queryset = User.objects.all()
        if request.query_params:
            name = request.query_params.get('name', None)
            email = request.query_params.get("email", None)
            page = request.query_params.get('page_size', None)
            if name:
                queryset = queryset.filter(name__icontains=name)
            if email:
                queryset = queryset.filter(email__icontains=email)
            # Paginate the queryset
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializers = UsersListSerializer(paginated_queryset, many=True)
            response = create_response_list_data(
                status=status.HTTP_200_OK,
                count=len(serializers.data),
                message=UserResponseMessage.USER_LIST_MESSAGE,
                data=serializers.data,
            )
            return Response(response, status=status.HTTP_200_OK)
        serializer = UsersListSerializer(queryset, many=True)
        response = create_response_list_data(
            status=status.HTTP_201_CREATED,
            count=len(serializer.data),
            message=UserLoginMessage.SIGNUP_SUCCESSFUL,
            data=serializer.data
        )
        return Response(response, status=status.HTTP_200_OK)


class UserDeleteView(APIView):
    permission_classes = [IsAdminUser]
    """
    This class is used to delete the user.
    """

    def delete(self, request, pk):
        try:
            user = User.objects.get(id=pk)
            user.is_active = False
            AddressDetails.objects.get(user_id=user.id)
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=UserResponseMessage.USER_DELETE_MESSAGE,
                data={}
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class UserUpdateProfileView(APIView):
    permission_classes = [IsAdminUser]
    """
    This class is used to update the user profile.
    """

    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=UserResponseMessage.PROFILE_UPDATED_SUCCESSFULLY,
                data={}
            )
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=serializer.errors,
                data={}
            )
            return Response(response_data, status=status.HTTP_200_OK)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny, ]
    """
    This class is used to login user's.
    """

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            resposne = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=UserLoginMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(resposne, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            response = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=UserLoginMessage.INCORRECT_PASSWORD,
                data={}
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        response_data = create_response_data(
            status=status.HTTP_201_CREATED,
            message=UserLoginMessage.SIGNUP_SUCCESSFUL,
            data={
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': str(user.phone),
                'is_email_verified': user.is_email_verified
            }
        )
        return Response(response_data, status=status.HTTP_201_CREATED)


class NonTeachingStaffCreateView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    """
    This class is used to create non teaching staff type user's.
    """

    def post(self, request):
        try:
            serializer = NonTeachingStaffSerializers(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_type = serializer.validated_data['user_type']
            image = serializer.validated_data['image']
            first_name = serializer.validated_data['first_name']
            last_name = serializer.validated_data['last_name']
            gender = serializer.validated_data['gender']
            dob = serializer.validated_data['dob']
            blood_group = serializer.validated_data['blood_group']
            religion = serializer.validated_data['religion']
            email = serializer.validated_data['email']
            phone = serializer.validated_data['phone']
            role = serializer.validated_data['role']
            address = serializer.validated_data['address']
            joining_date = serializer.validated_data['joining_date']
            ctc = serializer.validated_data['ctc']
            certificates = serializer.validated_data.get('certificate_files', [])

            if serializer.is_valid() == True:
                if user_type == 'non-teaching' or user_type == 'management' or user_type == 'payrollmanagement' or user_type == 'boarding':
                    user = User.objects.create_user(
                        name=first_name, email=email, phone=phone, user_type=user_type, school_id=request.user.school_id
                    )
                    user.save()
                    user_staff = StaffUser.objects.create(
                        user=user, first_name=first_name, last_name=last_name, gender=gender, image=image, dob=dob, blood_group=blood_group,
                        religion=religion, role=role, address=address,
                        joining_date=joining_date, ctc=ctc,
                    )
                    for cert_file in certificates:
                        Certificate.objects.create(user=user, certificate_file=cert_file)
                else:
                    raise ValidationError("Invalid user_type. Expected 'teacher'.")
            else:
                response = create_response_data(
                    status=status.HTTP_201_CREATED,
                    message=serializer.errors,
                    data={}
                )
                return Response(response, status=status.HTTP_201_CREATED)
            response_data = {
                'user_id': user_staff.id,
                'name': user.first_name,
                'email': user.email,
                'phone': str(user.phone),
                'user_type': user.user_type,
            }
            response = create_response_data(
                status=status.HTTP_201_CREATED,
                message=UserLoginMessage.SIGNUP_SUCCESSFUL,
                data=response_data
            )
            return Response(response, status=status.HTTP_201_CREATED)

        except ValidationError:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=serializer.errors,
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=UserResponseMessage.EMAIL_ALREADY_EXIST,
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class NonTeachingStaffListView(APIView):
    """
    This class is created to fetch the list of the non teaching staff.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        queryset = StaffUser.objects.filter(user__is_active=True, user__school_id=request.user.school_id).order_by("-id")
        if request.query_params:
            name = request.query_params.get('first_name', None)
            page = request.query_params.get('page_size', None)
            if name:
                queryset = queryset.filter(first_name__icontains=name)

            # Paginate the queryset
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializers = NonTeachingStaffListSerializers(paginated_queryset, many=True)
            response_data = {
                'status': status.HTTP_200_OK,
                'count': len(serializers.data),
                'message': UserResponseMessage.USER_LIST_MESSAGE,
                'data': serializers.data,
                'pagination': {
                    'page_size': paginator.page_size,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total_pages': paginator.page.paginator.num_pages,
                    'current_page': paginator.page.number,
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)

        serializer = NonTeachingStaffListSerializers(queryset, many=True)
        response = create_response_list_data(
            status=status.HTTP_200_OK,
            count=len(serializer.data),
            message=UserResponseMessage.USER_LIST_MESSAGE,
            data=serializer.data,
        )
        return Response(response, status=status.HTTP_200_OK)


class NonTeachingStaffDetailView(APIView):
    """
    This class is created to fetch the detail of the non teaching staff.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            data = StaffUser.objects.get(id=pk, user__school_id=request.user.school_id)
            if data.user.is_active == True:
                serializer = NonTeachingStaffDetailSerializers(data)
                response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=UserResponseMessage.USER_DETAIL_MESSAGE,
                    data=serializer.data
                )
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = create_response_data(
                    status=status.HTTP_404_NOT_FOUND,
                    message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                    data={}
                )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class NonTeachingStaffDeleteView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    """
    This class is used to delete the non teaching staff.
    """

    def delete(self, request, pk):
        try:
            teacher = StaffUser.objects.get(id=pk, user__school_id=request.user.school_id)
            user = User.objects.get(id=teacher.user_id)
            if teacher.user.user_type == "non-teaching":
                user.is_active = False
                user.save()
                response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=UserResponseMessage.USER_DELETE_MESSAGE,
                    data={}
                )
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response("Can't delete this user.")
        except StaffUser.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class NonTeachingStaffUpdateView(APIView):
    """
    This class is used to update the non teaching staff.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def patch(self, request, pk):
        try:
            files_data = []
            certificate_files = request.data.getlist('certificate_files')

            for file in certificate_files:
                files_data.append(file)
            data = {
                'email': request.data.get('email'),
                'phone': request.data.get('phone'),
                'first_name': request.data.get('first_name'),
                'last_name': request.data.get('last_name'),
                'dob': request.data.get('dob'),
                'image': request.data.get('image'),
                'gender': request.data.get('gender'),
                'joining_date': request.data.get('joining_date'),
                'religion': request.data.get('religion'),
                'blood_group': request.data.get('blood_group'),
                'ctc': request.data.get('ctc'),
                'experience': request.data.get('experience'),
                'role': request.data.get('role'),
                'address': request.data.get('address'),
                'highest_qualification': request.data.get('highest_qualification'),
                'certificate_files': files_data
            }
            staff = StaffUser.objects.get(id=pk, user__school_id=request.user.school_id)
            serializer = NonTeachingStaffProfileSerializers(staff, data=data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()

                # Update certificates separately
                if files_data:
                    staff.user.certificates.all().delete()  # Delete existing certificates
                    for cert_file_data in files_data:
                        Certificate.objects.create(user=staff.user, certificate_file=cert_file_data)
                response = create_response_data(
                    status=status.HTTP_200_OK,
                    message=UserResponseMessage.PROFILE_UPDATED_SUCCESSFULLY,
                    data={}
                )
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = create_response_data(
                    status=status.HTTP_200_OK,
                    message=serializer.errors,
                    data=serializer.errors
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except StaffUser.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class AttendanceCreateView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    """
    This class is used to marked non-teaching staff attendance.
    """
    def post(self, request):
        try:
            serializer = StaffAttendanceSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_data = create_response_data(
                    status=status.HTTP_201_CREATED,
                    message=AttendenceMarkedMessage.ATTENDENCE_MARKED_SUCCESSFULLY,
                    data=serializer.data,
                )
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data=serializer.errors
                )
                return Response(response, status=status.HTTP_200_OK)
        except ValidationError as e:
            response = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response, status=status.HTTP_200_OK)


class FetchAttendanceDetailView(APIView):
    """
    This class is created to fetch the detail of the teacher attendance.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            staff = StaffUser.objects.get(id=pk)
            data = StaffAttendence.objects.filter(staff_id=pk).order_by('-date')

            filter_type = request.query_params.get('filter_type', None)
            if filter_type:
                today = datetime.date.today()
                if filter_type == 'weekly':
                    start_date = today - datetime.timedelta(days=today.weekday())
                    end_date = start_date + datetime.timedelta(days=6)
                elif filter_type == 'monthly':
                    start_date = today.replace(day=1)
                    end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
                elif filter_type == 'yearly':
                    start_date = today.replace(month=1, day=1)
                    end_date = today.replace(month=12, day=31)
                data = data.filter(date__range=(start_date, end_date))

            start_date = request.query_params.get('start_date', None)
            date = request.query_params.get('date', None)
            end_date = request.query_params.get('end_date', None)
            if start_date and end_date:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
                data = data.filter(date__range=(start_date, end_date))
            if date:
                date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                data = data.filter(date=(date))

            if data:
                serializer = StaffAttendanceDetailSerializer(data, many=True)
                response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=UserResponseMessage.USER_DETAIL_MESSAGE,
                    data={
                        "staff_name": f"{staff.first_name} {staff.last_name}",
                        "staff_id": staff.id,
                        "staff_role": staff.role,
                        "total_attendance": get_staff_total_attendance(data),
                        "monthly_attendance": get_staff_monthly_attendance(data),
                        "total_absent": get_staff_total_absent(data),
                        "monthly_absent": get_staff_monthly_absent(data),
                        "attendence_detail": serializer.data,
                    }
                )
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = create_response_data(
                    status=status.HTTP_404_NOT_FOUND,
                    message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                    data={}
                )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class FetchAttendanceListView(APIView):
    """
    This class is created to fetch the list of the teacher's attendance.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        queryset = StaffUser.objects.filter(user__is_active=True)
        if request.query_params:
            name = request.query_params.get('first_name', None)
            page = request.query_params.get('page_size', None)
            if name:
                queryset = queryset.filter(first_name__icontains=name)

            # Paginate the queryset
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializers = StaffAttendanceListSerializer(paginated_queryset, many=True)
            response_data = {
                'status': status.HTTP_200_OK,
                'count': len(serializers.data),
                'message': UserResponseMessage.USER_LIST_MESSAGE,
                'data': serializers.data,
                'pagination': {
                    'page_size': paginator.page_size,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total_pages': paginator.page.paginator.num_pages,
                    'current_page': paginator.page.number,
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)

        serializer = StaffAttendanceListSerializer(queryset, many=True)
        response = create_response_list_data(
            status=status.HTTP_200_OK,
            count=len(serializer.data),
            message=UserResponseMessage.USER_LIST_MESSAGE,
            data=serializer.data,
        )
        return Response(response, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    This class is created to logout the login user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            serializer = LogoutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        except AuthenticationFailed as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'User logged out successfully'}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    This class is created to fetch detail of the user profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if user.user_type == 'teacher':
                teacher_user = TeacherUser.objects.get(user=user)
                user_detail = TeacherUserProfileSerializer(teacher_user)
            elif user.user_type == "student":
                student_user = StudentUser.objects.get(user=user)
                user_detail = StudentUserProfileSerializer(student_user)
            elif user.user_type == "non-teaching":
                staff_user = StaffUser.objects.get(user=user)
                user_detail = NonTeachingStaffDetailSerializers(staff_user)
            # Fetch unread notifications for the user
            notifications = Notification.objects.filter(reciver_id=user.id, is_read__in=[0,1])
            # Serialize notifications
            notification_serializer = NotificationSerializer(notifications, many=True)
        except (StudentUser.DoesNotExist, TeacherUser.DoesNotExist, StaffUser.DoesNotExist):
            response = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=UserLoginMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        response_data = {
            "status": status.HTTP_201_CREATED,
            "message": UserLoginMessage.USER_LOGIN_SUCCESSFUL,
            "notification": len(notification_serializer.data),
            "data": user_detail.data
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class TeacherUserScheduleView(APIView):
    """
    This class is created to fetch schedule of the teacher.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            user = request.user
            if user.user_type == 'teacher':
                today = datetime.date.today()
                teacher = TeacherUser.objects.get(user=user.id, user__school_id=request.user.school_id)
                data = TeachersSchedule.objects.filter(teacher=teacher.id, school_id=request.user.school_id,start_date__lte=today, end_date__gte=today)
                if data:
                    serializer = TeacherUserScheduleSerializer(data[0])
                    response_data = create_response_data(
                        status=status.HTTP_200_OK,
                        message=ScheduleMessage.SCHEDULE_FETCHED_SUCCESSFULLY,
                        data=serializer.data
                    )
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    response_data = create_response_data(
                        status=status.HTTP_404_NOT_FOUND,
                        message=ScheduleMessage.SCHEDULE_NOT_FOUND,
                        data={}
                    )
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message='you are not an teacher user.',
                    data={}
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class TeacherCurriculumListView(APIView):
    """
    This class is created to fetch the list of classes, sections, and subject.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            user = request.user
            if user.user_type == 'teacher':
                curriculum = Curriculum.objects.filter()
                serializer = CurriculumTeacherListerializer(curriculum, many=True)

                classes = list(set([item['class_name'] for item in serializer.data]))
                # sections = list(set([item['section'] for item in serializer.data]))
                # subject_names = list(set([subject['subject_name'] for item in serializer.data for subject in item['subject_name_code']]))

                response = {
                    'classes': classes,
                    # 'sections': sections,
                    # 'subjects': subject_names
                }
                response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=CurriculumMessage.CURRICULUM_LIST_MESSAGE,
                    data=response
                )
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="you are not an teacher user.",
                    data={}
                )
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherCurriculumClassListView(APIView):
    """
    This class is created to fetch the list of sections in the provided class.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            user = request.user
            if user.user_type == 'teacher':
                class_name = request.query_params.get('class_name')
                curriculum = Curriculum.objects.filter(school_id=request.user.school_id, class_name=class_name)
                serializer = CurriculumTeacherListerializer(curriculum, many=True)

                # classes = list(set([item['class_name'] for item in serializer.data]))
                sections = list(set([item['section'] for item in serializer.data]))
                # subject_names = list(set([subject['subject_name'] for item in serializer.data for subject in item['subject_name_code']]))
                #
                response = {
                    'sections': sections,
                }
                response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=CurriculumMessage.CURRICULUM_LIST_MESSAGE,
                    data=response
                )
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="you are not an teacher user.",
                    data={}
                )
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherCurriculumSubjectListView(APIView):
    """
    This class is created to fetch the list of subject in the provided setion.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            user = request.user
            if user.user_type == 'teacher':
                class_name = request.query_params.get('class_name')
                section = request.query_params.get('section')
                curriculum = Curriculum.objects.filter(school_id=request.user.school_id, class_name=class_name, section=section)
                serializer = CurriculumTeacherListerializer(curriculum, many=True)

                # classes = list(set([item['class_name'] for item in serializer.data]))
                # sections = list(set([item['section'] for item in serializer.data]))
                subject_names = list(set([subject['subject_name'] for item in serializer.data for subject in item['subject_name_code']]))
                #
                response = {
                    'subject_name': subject_names,
                }
                response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=CurriculumMessage.CURRICULUM_LIST_MESSAGE,
                    data=response
                )
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="you are not an teacher user.",
                    data={}
                )
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TeacherDayReviewView(APIView):
    """
    This class is Used to create teacher day & review.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        try:
            user = request.user
            if user.user_type == "teacher":

                serializer = DayReviewSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save(school_id=request.user.school_id)
                    response_data = create_response_data(
                        status=status.HTTP_201_CREATED,
                        message=DayReviewMessage.DAY_REVIEW_CREATED_SUCCESSFULLY,
                        data=serializer.data,
                    )
                    return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message='you are not an teacher user.',
                    data={}
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            response = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response, status=status.HTTP_200_OK)


class TeacherDayReviewDetailView(APIView):
    """
    This colass is used to fetch detail of teacher day & review.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            data = DayReview.objects.get(id=pk, school_id=request.user.school_id)
            serializer = DayReviewDetailSerializer(data)
            response_data = create_response_data(
                        status=status.HTTP_201_CREATED,
                        message=DayReviewMessage.DAY_REVIEW_FETCHED_SUCCESSFULLY,
                        data=serializer.data,
                    )
            return Response(response_data, status=status.HTTP_200_OK)
        except DayReview.DoesNotExist:
            resposne = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=DayReviewMessage.DAY_REVIEW_NOT_FOUND,
                data={}
            )
            return Response(resposne, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            response = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class TeacherDayReviewListView(APIView):
    """
    This class is created to fetch the list of the teacher's day & review.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        queryset = DayReview.objects.all()
        if request.query_params:
            updated_at = request.query_params.get('updated_at', None)
            if updated_at:
                queryset = queryset.filter(updated_at__date=updated_at)

            # Paginate the queryset
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializers = DayReviewDetailSerializer(paginated_queryset, many=True)
            response_data = {
                'status': status.HTTP_200_OK,
                'count': len(serializers.data),
                'message': ScheduleMessage.SCHEDULE_LIST_MESSAGE,
                'data': serializers.data,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        serializer = DayReviewDetailSerializer(queryset, many=True)
        response = create_response_list_data(
            status=status.HTTP_200_OK,
            count=len(serializer.data),
            message=ScheduleMessage.SCHEDULE_LIST_MESSAGE,
            data=serializer.data,
        )
        return Response(response, status=status.HTTP_200_OK)


class FetchTeacherAttendanceView(APIView):
    """
    This class is used to fetch attendance list of teacher according to provided month
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            user = request.user
            teacher = TeacherUser.objects.get(user=user.id)
            month = request.query_params.get('month', None)

            if month:
                month = int(month)
                current_year = datetime.date.today().year

                _, last_day = calendar.monthrange(current_year, month)
                start_date = datetime.date(current_year, month, 1)
                end_date = datetime.date(current_year, month, last_day)
                data = TeacherAttendence.objects.filter(teacher_id=teacher.id, date__range=[start_date, end_date], teacher__user__school_id=request.user.school_id)
            else:
                data = TeacherAttendence.objects.filter(teacher_id=teacher.id, teacher__user__school_id=request.user.school_id)
            serializer = TeacherUserAttendanceListSerializer(data, many=True)

            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=AttendenceMarkedMessage.ATTENDANCE_FETCHED_SUCCESSFULLY,
                data=serializer.data,
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=str(e),
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class NotificationCreateView(APIView):
    """
    This class is used to create notification.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            serializer = NotificationSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_data = create_response_data(
                    status=status.HTTP_201_CREATED,
                    message=NotificationMessage.NOTIFICATION_CREATED_SUCCESSFULLY,
                    data={},
                )
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data={},
                )
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class NotificationListView(APIView):
    """
    This class is used to fetch the list of the notification.
    """
    permission_classes = [permissions.IsAuthenticated, IsInSameSchool]

    def get(self, request):
        data = Notification.objects.filter(reciver_id=request.user.id, is_read__in=[0, 1])
        data.update(is_read=1)
        serializer = NotificationListSerializer(data, many=True)
        response_data = create_response_data(
                status=status.HTTP_201_CREATED,
                message=NotificationMessage.NOTIFICATION_FETCHED_SUCCESSFULLY,
                data=serializer.data,
            )
        return Response(response_data, status=status.HTTP_200_OK)


class NotificationDeleteView(APIView):
    """
    This class is used to clear notifications.
    """
    permission_classes = [permissions.IsAuthenticated, IsInSameSchool]

    def post(self, request):
        receiver = request.user

        notifications = Notification.objects.filter(reciver_id=receiver.id)
        notifications.update(is_read=2)
        response_data = create_response_data(
            status=status.HTTP_201_CREATED,
            message="All notifications cleared successfully.",
            data={},
        )
        return Response(response_data, status=status.HTTP_200_OK)


class AnnouncementCreateView(APIView):
    """
    This class is used to create announcement.
    """
    permission_classes = [IsSuperAdminUser]

    def post(self, request):
        try:
            serializer = AnnouncementCreateSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response_data = create_response_data(
                    status=status.HTTP_201_CREATED,
                    message=AnnouncementMessage.ANNOUNCEMENT_CREATED_SUCCESSFULLE,
                    data={},
                )
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data={},
                )
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class AnnouncementListView(APIView):
    """
    This class is used to fetch the list of the Announcement.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = Announcement.objects.all().order_by('-id')
        serializer = AnnouncementListSerializer(data, many=True)
        response_data = create_response_data(
                status=status.HTTP_201_CREATED,
                message=AnnouncementMessage.ANNOUNCEMENT_FETCHED_SUCCESSFULLE,
                data=serializer.data,
            )
        return Response(response_data, status=status.HTTP_200_OK)


class CreateTimetableView(APIView):
    """
    This class is used to create exam timetable for the students.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        try:
            if request.user.user_type == 'teacher':
                more_subject = request.data.get('more_subject')
                # more_subject_str = json.loads(more_subject)
                # data = {
                #     "class_name": request.data.get("class_name"),
                #     "class_section": request.data.get("class_section"),
                #     "exam_type": request.data.get("exam_type"),
                #     "exam_month": request.data.get("exam_month"),
                #     "more_subject": more_subject_str,
                # }

                serializer = CreateTimeTableSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save(school_id=request.user.school_id)
                    response_data = create_response_data(
                        status=status.HTTP_201_CREATED,
                        message=TimeTableMessage.TIMETABLE_CREATED_SUCCESSFULLY,
                        data=serializer.data,
                    )
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    response_data = create_response_data(
                        status=status.HTTP_400_BAD_REQUEST,
                        message=serializer.errors,
                        data={},
                    )
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message='you are not an teacher user.',
                    data={}
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class UndeclaredTimetableView(APIView):
    """
    This class is used to fetch the list of the undeclared timetable.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            data = TimeTable.objects.filter(status=0, school_id=request.user.school_id).order_by('-id')
            serializer = TimeTableListSerializer(data, many=True)
            response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=TimeTableMessage.UNDECLARED_TIMETABLE_FETCHED_SUCCESSFULLY,
                    data=serializer.data,
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class DeclaredTimetableView(APIView):
    """
    This class is used to fetch the list of the declared timetable.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            data = TimeTable.objects.filter(status=1, school_id=request.user.school_id).order_by('-id')
            serializer = TimeTableListSerializer(data, many=True)
            response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=TimeTableMessage.DECLARED_TIMETABLE_FETCHED_SUCCESSFULLY,
                    data=serializer.data,
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class TimetableDetailView(APIView):
    """
    This class is used to fetch the detail of the timetable according to provided id.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            data = TimeTable.objects.get(id=pk, school_id=request.user.school_id)
            serializer = TimeTableDetailSerializer(data)
            response_data = create_response_data(
                        status=status.HTTP_200_OK,
                        message=TimeTableMessage.TIMETABLE_FETCHED_SUCCESSFULLY,
                        data=serializer.data,
                    )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=TimeTableMessage.TIMETABLE_NOT_EXIST,
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class TimetableDeleteView(APIView):
    permission_classes = [IsTeacherUser, IsInSameSchool]
    """
    This class is used to delete the timetable.
    """

    def delete(self, request, pk):
        try:
            time_table_data = TimeTable.objects.get(id=pk, school_id=request.user.school_id)
            time_table_data.delete()
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=TimeTableMessage.TIMETABLE_DELETED_SUCCESSFULLY,
                data={}
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except TimeTable.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=TimeTableMessage.TIMETABLE_NOT_EXIST,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class TimetableUpdateView(APIView):
    """
    This class is used to update the timetable.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def patch(self, request, pk):
        try:
            student = TimeTable.objects.get(id=pk, school_id=request.user.school_id)
            # more_subject = request.data.get('more_subject')
            # more_subject_str = json.loads(more_subject)
            # data = {
            #     "class_name": request.data.get("class_name"),
            #     "class_section": request.data.get("class_section"),
            #     "exam_type": request.data.get("exam_type"),
            #     "exam_month": request.data.get("exam_month"),
            #     "more_subject": more_subject_str,
            # }
            serializer = TimeTableUpdateSerializer(student, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response = create_response_data(
                    status=status.HTTP_200_OK,
                    message=TimeTableMessage.TIMETABLE_UPDATED_SUCCESSFULLY,
                    data=serializer.data
                )
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data=serializer.errors
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except TimeTable.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=TimeTableMessage.TIMETABLE_NOT_EXIST,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class DeclareTimetableView(APIView):
    """
    This class is used to declare timetable.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        try:
            data = TimeTable.objects.filter(status=0, school_id=request.user.school_id)
            data.update(status=1)
            response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=TimeTableMessage.TIMETABLE_DECLARE_SUCCESSFULLY,
                    data={},
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class CreateExamReportView(APIView):
    """
    This class is used to create exam report of the students.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        try:
            if request.user.user_type == 'teacher':
                serializer = ExamReportCreateSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save(school_id=request.user.school_id)
                    response_data = create_response_data(
                        status=status.HTTP_201_CREATED,
                        message=ReportCardMesssage.REPORT_CARD_CREATED_SUCCESSFULLY,
                        data=serializer.data,
                    )
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    response_data = create_response_data(
                        status=status.HTTP_400_BAD_REQUEST,
                        message=serializer.errors,
                        data={},
                    )
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message='you are not an teacher user.',
                    data={}
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class DeclareExamReportView(APIView):
    """
    This class is used to declare exam report.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        try:
            data = ExmaReportCard.objects.filter(status=0, school_id=request.user.school_id)
            data.update(status=1)
            response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=ReportCardMesssage.REPORT_CARD_DECLARE_SUCCESSFULLY,
                    data={},
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class DeclaredExamReportListView(APIView):
    """
    This class is used to fetch the list of the declared exam report.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            data = ExmaReportCard.objects.filter(status=1, school_id=request.user.school_id).order_by('-id')
            serializer = ExamReportListSerializer(data, many=True)
            response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=ReportCardMesssage.DECLARED_REPORT_CARD_FETCHED_SUCCESSFULLY,
                    data=serializer.data,
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class UndeclaredExamReportListView(APIView):
    """
    This class is used to fetch the list of the undeclared exam report.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            data = ExmaReportCard.objects.filter(status=0, school_id=request.user.school_id).order_by('-id')
            serializer = ExamReportListSerializer(data, many=True)
            response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=ReportCardMesssage.UNDECLARED_REPORT_CARD_FETCHED_SUCCESSFULLY,
                    data=serializer.data,
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class ExamReportCardDeleteView(APIView):
    permission_classes = [IsTeacherUser, IsInSameSchool]
    """
    This class is used to delete the exam report card.
    """

    def delete(self, request, pk):
        try:
            report_card_data = ExmaReportCard.objects.get(id=pk, school_id=request.user.school_id)
            report_card_data.delete()
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=ReportCardMesssage.REPORT_CARD_DELETED_SUCCESSFULLY,
                data={}
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except ExmaReportCard.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=ReportCardMesssage.REPORT_CARD_NOT_EXIST,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class ExamReportCardDetailView(APIView):
    """
    This class is used to fetch the detail of the exam report card according to provided id.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            data = ExmaReportCard.objects.get(id=pk, school_id=request.user.school_id)
            serializer = ExamReportCardViewSerializer(data)
            response_data = create_response_data(
                        status=status.HTTP_200_OK,
                        message=ReportCardMesssage.REPORT_CARD_FETCHED_SUCCESSFULLY,
                        data=serializer.data,
                    )
            return Response(response_data, status=status.HTTP_200_OK)
        except ExmaReportCard.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=ReportCardMesssage.REPORT_CARD_NOT_EXIST,
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class ExamReportCardUpdateView(APIView):
    """
    This class is used to update the exam report card.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def patch(self, request, pk):
        try:
            exam_report_card = ExmaReportCard.objects.get(id=pk, school_id=request.user.school_id)
            serializer = ExamReportcardUpdateSerializer(exam_report_card, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response = create_response_data(
                    status=status.HTTP_200_OK,
                    message=ReportCardMesssage.REPORT_CARD_UPDATED_SUCCESSFULLY,
                    data=serializer.data
                )
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data=serializer.errors
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except ExmaReportCard.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=ReportCardMesssage.REPORT_CARD_NOT_EXIST,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class CreateZoomLinkView(APIView):
    """
    This class is used to create zoom link.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        try:
            serializer = ZoomLinkCreateSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(school_id=request.user.school_id)
                response_data = create_response_data(
                status=status.HTTP_201_CREATED,
                message=ZoomLinkMessage.ZOOM_LINK_UPLOADED_SUCCESSFULLY,
                data={}
                )
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data={}
                )
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class ZoomLinkListView(APIView):
    """
    This class is used to fetch list of the uploaded zoom link's.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            current_date_time_ist = timezone.localtime(timezone.now(), pytz_timezone('Asia/Kolkata'))
            # current_time = current_date_time_ist.strftime("%I:%M %p")

            current_date = current_date_time_ist.date()
            currunt_time_str = current_date_time_ist.time()
            data = ZoomLink.objects.filter(school_id=request.user.school_id, date__gte=current_date, end_time__gt=currunt_time_str).order_by("date")

            # sorted(data, key=lambda x: abs((x.date - current_date).days))
            serializer = ZoomLinkListSerializer(data, many=True)
            response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=ZoomLinkMessage.ZOOM_LINK_FETCHED_SUCCESSFULLY,
                    data=serializer.data
                    )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            create_response_data(
                status=status.HTTP_200_OK,
                message=e.args[0],
                data={}
            )


class UploadStudyMaterialView(APIView):
    """
    This class is used to upload study material.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        try:
            serializer = StudyMaterialUploadSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(school_id=request.user.school_id)
                response_data = create_response_data(
                        status=status.HTTP_201_CREATED,
                        message=StudyMaterialMessage.STUDY_MATERIAL_UPLOADED_SUCCESSFULLY,
                        data=serializer.data
                        )
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data={}
                )
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            response = create_response_data(
                status=status.HTTP_401_UNAUTHORIZED,
                message=UserResponseMessage.TOKEN_HAS_EXPIRED,
                data={}
            )
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)


class StudyMaterialListView(APIView):
    """
    This class is used to fetch list of study material.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request):
        try:
            data = StudentMaterial.objects.filter(school_id=request.user.school_id)
            serializer = StudyMaterialListSerializer(data, many=True)
            response_data = create_response_data(
                            status=status.HTTP_200_OK,
                            message=StudyMaterialMessage.STUDY_MATERIAL_FETCHED_SUCCESSFULLY,
                            data=serializer.data
                            )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            response = create_response_data(
                status=status.HTTP_401_UNAUTHORIZED,
                message=UserResponseMessage.TOKEN_HAS_EXPIRED,
                data={}
            )
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)


class StudyMaterialDetailView(APIView):
    """
    This class is used to fetch detail of the study material.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            data = StudentMaterial.objects.get(id=pk, school_id=request.user.school_id)
            serializer = StudyMaterialDetailSerializer(data)
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=StudyMaterialMessage.STUDY_MATERIAL_FETCHED_SUCCESSFULLY,
                data=serializer.data,
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except StudentMaterial.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=StudyMaterialMessage.STUDY_MATERIAL_Not_Exist,
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            response = create_response_data(
                status=status.HTTP_401_UNAUTHORIZED,
                message=UserResponseMessage.TOKEN_HAS_EXPIRED,
                data={}
            )
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

class EventCreateView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(school_id=request.user.school_id)
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=EventsMessages.EVENT_CREATED_SUCCESSFULLY,
                data=serializer.data,
            )
            return Response(response_data, status=status.HTTP_200_OK)
        response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=serializer.errors,
                data={},
            )
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
class GetAllEvents(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        is_one_day_event = request.query_params.get('is_one_day_event')
        is_event_calendar = request.query_params.get('is_event_calendar')

        if not start_date or not end_date:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=EventsMessages.EVENT_PROVIDE_ALL_INFORMATION,
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date or not end_date:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=EventsMessages.PROVIDE_VALID_DATE,
                data={},
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        events = EventsCalender.objects.filter(start_date__gte=start_date, end_date__lte=end_date, school_id=request.user.school_id)

        if is_one_day_event is not None:
            events = events.filter(is_one_day_event=is_one_day_event.lower() == 'true')
        if is_event_calendar is not None:
            events = events.filter(is_event_calendar=is_event_calendar.lower() == 'true')

        serializer = EventsCalendarSerializer(events, many=True)
        response_data = create_response_data(
            status=status.HTTP_200_OK,
            message=EventsMessages.EVENTS_DATA_FETCHED_SUCCESSFULLY,
            data=serializer.data,
        )
        return Response(response_data, status=status.HTTP_200_OK)