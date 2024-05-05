import calendar
import datetime
import json

from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import User, Class, AddressDetails, StudentUser, TeacherUser
from authentication.permissions import IsSuperAdminUser, IsAdminUser, IsStudentUser, IsTeacherUser, IsInSameSchool
from constants import UserLoginMessage, UserResponseMessage, AttendenceMarkedMessage, CurriculumMessage
from curriculum.models import Curriculum, Subjects
from pagination import CustomPagination
from student.models import StudentAttendence
from student.serializers import StudentUserSignupSerializer, StudentDetailSerializer, StudentListSerializer, \
    studentProfileSerializer, StudentAttendanceDetailSerializer, \
    StudentAttendanceListSerializer, StudentListBySectionSerializer, StudentAttendanceCreateSerializer, AdminClassListSerializer, AdminOptionalSubjectListSerializer, StudentAttendanceSerializer
from utils import create_response_data, create_response_list_data, get_student_total_attendance, \
    get_student_total_absent, get_student_attendence_percentage, generate_random_password


class StudentUserCreateView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    """
    This class is used to create student type user's.
    """

    def post(self, request):
        try:
            serializer = StudentUserSignupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            name = serializer.validated_data['name']
            email = serializer.validated_data.get('email', '')
            user_type = serializer.validated_data.get('user_type', '')

            dob = serializer.validated_data['dob']
            image = serializer.validated_data['image']
            father_name = serializer.validated_data.get('father_name', '')
            father_phone_number = serializer.validated_data.get('father_phone_number', '')
            mother_name = serializer.validated_data.get('mother_name', '')
            mother_occupation = serializer.validated_data.get('mother_occupation', '')
            mother_phone_number = serializer.validated_data.get('mother_phone_number', '')
            gender = serializer.validated_data['gender']
            father_occupation = serializer.validated_data.get('father_occupation', '')
            admission_date = serializer.validated_data['admission_date']
            school_fee = serializer.validated_data.get('school_fee', '')
            bus_fee = serializer.validated_data.get('bus_fee', '')
            canteen_fee = serializer.validated_data.get('canteen_fee', '')
            other_fee = serializer.validated_data.get('other_fee', '')
            due_fee = serializer.validated_data.get('due_fee', '')
            total_fee = serializer.validated_data.get('total_fee', '')
            religion = serializer.validated_data['religion']
            blood_group = serializer.validated_data.get('blood_group', '')
            class_enrolled = serializer.validated_data['class_enrolled']
            section = serializer.validated_data['section']
            permanent_address = serializer.validated_data.get('permanent_address', '')
            bus_number = serializer.validated_data.get('bus_number', '')
            bus_route = serializer.validated_data.get('bus_route', '')
            curriculum_data = serializer.validated_data['curriculum']
            enrollment_no = serializer.validated_data.get('enrollment_no', '')
            roll_no = serializer.validated_data.get('roll_no', '')
            guardian_no = serializer.validated_data.get('guardian_no', '')
            optional_subject = serializer.validated_data.get('optional_subject', '')

            # try:
            #     curriculum = Curriculum.objects.get(id=curriculum_data)
            #     serializer.validated_data['curriculum'] = curriculum
            # except Curriculum.DoesNotExist:
            #     return Response({"message": "Curriculum not found"}, status=status.HTTP_404_NOT_FOUND)

            if user_type == 'student' and serializer.is_valid() == True:
                user = User.objects.create_user(
                    name=name, email=email, user_type=user_type, school_id=request.user.school_id
                )
                password = generate_random_password()
                user.set_password(password)
                user.save()
                user_student = StudentUser.objects.create(
                    user=user, name=name, dob=dob, image=image, father_name=father_name, mother_name=mother_name,
                    gender=gender, father_occupation=father_occupation, religion=religion,
                    admission_date=admission_date,
                    school_fee=school_fee, bus_fee=bus_fee, canteen_fee=canteen_fee, other_fee=other_fee,
                    total_fee=total_fee, blood_group=blood_group, class_enrolled=class_enrolled, father_phone_number=father_phone_number,
                    mother_occupation=mother_occupation, mother_phone_number=mother_phone_number, section=section, permanent_address=permanent_address,
                    bus_number=bus_number, bus_route=bus_route, due_fee=due_fee, curriculum=curriculum_data, enrollment_no=enrollment_no, roll_no=roll_no,
                    guardian_no=guardian_no, optional_subject=optional_subject
                )
            else:
                raise ValidationError("Invalid user_type. Expected 'student'.")
            response_data = {
                'user_id': user_student.id,
                'name': user_student.name,
                'email': user.email,
                'user_type': user.user_type,
                'password': password
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


class FetchStudentDetailView(APIView):
    """
    This class is created to fetch the detail of the student.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            data = StudentUser.objects.get(id=pk, user__school_id=request.user.school_id)
            if data.user.is_active == True:
                serializer = StudentDetailSerializer(data)
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
        except StudentUser.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=str(e.args[0]),
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class StudentListView(APIView):
    """
    This class is created to fetch the list of the student's.
    """
    permission_classes = [IsAdminUser,IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        queryset = StudentUser.objects.filter(user__is_active=True, user__school_id=request.user.school_id).order_by("-id")
        if request.query_params:
            name = request.query_params.get('name', None)
            page = request.query_params.get('page_size', None)
            if name:
                queryset = queryset.filter(user__name__icontains=name)

            # Paginate the queryset
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializers = StudentListSerializer(paginated_queryset, many=True)
            response_data = {
                'status': status.HTTP_201_CREATED,
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
            return Response(response_data, status=status.HTTP_201_CREATED)
        serializer = StudentListSerializer(queryset, many=True)
        response = create_response_list_data(
            status=status.HTTP_200_OK,
            count=len(serializer.data),
            message=UserResponseMessage.USER_LIST_MESSAGE,
            data=serializer.data,
        )
        return Response(response, status=status.HTTP_200_OK)


class StudentDeleteView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    """
    This class is used to delete the student.
    """

    def delete(self, request, pk):
        try:
            student = StudentUser.objects.get(id=pk, user__school_id=request.user.school_id)
            user = User.objects.get(id=student.user_id)
            if student.user.user_type == "student":
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
        except StudentUser.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class StudentUpdateProfileView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    """
    This class is used to update the student profile.
    """

    def patch(self, request, pk):
        try:
            student = StudentUser.objects.get(id=pk, user__school_id=request.user.school_id)
            serializer = studentProfileSerializer(student, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                response = create_response_data(
                    status=status.HTTP_200_OK,
                    message=UserResponseMessage.PROFILE_UPDATED_SUCCESSFULLY,
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
        except StudentUser.DoesNotExist:
            response_data = create_response_data(
                status=status.HTTP_404_NOT_FOUND,
                message=UserResponseMessage.USER_DOES_NOT_EXISTS,
                data={}
            )
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)


class ClassStudentListView(APIView):
    permission_classes = [IsAdminUser, IsInSameSchool]
    """
    This class is used to create attendance of student's.
    """
    def get(self, request):
        try:
            current_date = timezone.now().date()
            curriculum_data = Curriculum.objects.filter(school_id=request.user.school_id).values('class_name', 'section').distinct()
            class_teacher_info = []
            for data in curriculum_data:
                class_name = data['class_name']
                section = data['section']
                teacher_info = TeacherUser.objects.filter(class_subject_section_details__0__class=class_name, class_subject_section_details__0__section=section,
                                                          user__school_id=request.user.school_id).values('full_name')
                class_teacher_info.append({
                    'class_name': class_name,
                    'section': section,
                    'teachers': [teacher['full_name'] for teacher in teacher_info]
                })

            class_student_count = []
            for data in curriculum_data:
                class_name = data['class_name']
                section = data['section']
                student_count = StudentUser.objects.filter(class_enrolled=class_name, section=section, user__school_id=request.user.school_id).count()
                class_student_count.append({
                    'class_name': class_name,
                    'section': section,
                    'student_count': student_count
                })
            class_attendance_info = []
            for data in curriculum_data:
                class_name = data['class_name']
                section = data['section']
                total_present = StudentAttendence.objects.filter(date=current_date, student__class_enrolled=class_name, student__section=section,
                                                                 mark_attendence='P').count()
                total_absent = StudentAttendence.objects.filter(date=current_date, student__class_enrolled=class_name, student__section=section,
                                                                mark_attendence='A').count()
                class_attendance_info.append({
                    'class_name': class_name,
                    'section': section,
                    'total_present': total_present,
                    'total_absent': total_absent
                })

            response_data = []
            for curriculum_info, teacher_info, student_info, attendance_info in zip(curriculum_data, class_teacher_info,
                                                                   class_student_count, class_attendance_info):
                response_data.append({
                    'class': curriculum_info['class_name'],
                    'section': curriculum_info['section'],
                    'class_teacher': teacher_info['teachers'],
                    'class_strength': student_info['student_count'],
                    'total_present': attendance_info['total_present'],
                    'total_absent': attendance_info['total_absent']
                })

            response = {
                "status": status.HTTP_200_OK,
                "message": CurriculumMessage.CURRICULUM_LIST_MESSAGE,
                "date": current_date,
                "data": response_data
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class FetchAttendanceDetailView(APIView):
    """
    This class is created to fetch the detail of the student attendance.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def get(self, request, pk):
        try:
            student = StudentUser.objects.get(id=pk, user__school_id=request.user.school_id)
            data = StudentAttendence.objects.filter(student_id=pk, student__user__school_id=request.user.school_id).order_by('-date')

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
                serializer = StudentAttendanceDetailSerializer(data, many=True)
                response_data = create_response_data(
                    status=status.HTTP_200_OK,
                    message=UserResponseMessage.USER_DETAIL_MESSAGE,
                    data={
                        "student_name": student.name,
                        "student_roll_no": student.id,
                        "class": student.class_enrolled,
                        "section": student.section,
                        "total_attendance": get_student_total_attendance(data),
                        "total_absent": get_student_total_absent(data),
                        "total_percentage": f"{get_student_attendence_percentage(data)}%",
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
    This class is created to fetch the list of the student attendance according to class.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            class_name = request.query_params.get('class_name')
            section = request.query_params.get('section')
            current_date = timezone.now().date()
            students = StudentUser.objects.filter(class_enrolled=class_name, section=section, user__school_id=request.user.school_id)
            attendance_data = StudentAttendence.objects.filter(date=current_date, student__in=students, student__user__school_id=request.user.school_id)

            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(attendance_data, request)

            serializers = StudentAttendanceListSerializer(result_page, many=True)

            response_data = []
            for attendance in serializers.data:
                response_data.append({
                    'student_id': attendance['student'].id,
                    'student_name': attendance['student'].name,
                    'roll_number': attendance['student'].roll_no,
                    'class': attendance['student'].class_enrolled,
                    'section': attendance['student'].section,
                    'marked_attendance': attendance['mark_attendence'],
                    'attendance_percentage': attendance['percentage'],
                    'total_attendance': attendance['total_attendance'],
                })
            response = {
                'status': status.HTTP_200_OK,
                'message': AttendenceMarkedMessage.STUDENT_ATTENDANCE_FETCHED_SUCCESSFULLY,
                'data': response_data,
                'pagination': {
                    'page_size': paginator.page_size,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total_pages': paginator.page.paginator.num_pages,
                    'current_page': paginator.page.number,
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class FetchAttendanceFilterListView(APIView):
    """
    This class is created to fetch the list of the student attendance according to filter value.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            class_name = request.data.get('class_name')
            section = request.data.get('section')
            students = StudentUser.objects.filter(class_enrolled=class_name, section=section, user__school_id=request.user.school_id)
            attendance_data = StudentAttendence.objects.filter(student__in=students, student__user__school_id=request.user.school_id)

            date = request.query_params.get('date', None)
            mark_attendence = request.query_params.get('mark_attendence', None)
            if date:
                date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                attendance_data = attendance_data.filter(date=date)
            if mark_attendence == 'A':
                attendance_data = attendance_data.filter(mark_attendence='A')
            if mark_attendence == 'P':
                attendance_data = attendance_data.filter(mark_attendence='P')
            if mark_attendence == 'L':
                attendance_data = attendance_data.filter(mark_attendence='L')

            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(attendance_data, request)

            serializers = StudentAttendanceListSerializer(result_page, many=True)
            response_data = []
            for attendance in serializers.data:
                response_data.append({
                    'student_id': attendance['student'].id,
                    'student_name': attendance['student'].name,
                    'roll_number': attendance['student'].roll_no,
                    'class': attendance['student'].class_enrolled,
                    'section': attendance['student'].section,
                    'marked_attendance': attendance['mark_attendence'],
                    'attendance_percentage': attendance['percentage'],
                    'total_attendance': attendance['total_attendance'],
                })
            response={
                'status': status.HTTP_200_OK,
                'message': AttendenceMarkedMessage.STUDENT_ATTENDANCE_FETCHED_SUCCESSFULLY,
                'data': response_data,
                'pagination': {
                    'page_size': paginator.page_size,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total_pages': paginator.page.paginator.num_pages,
                    'current_page': paginator.page.number,
                }
            }
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class FetchStudentList(APIView):
    """
    This class is created to fetch the list of the student's according to section.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]
    pagination_class = CustomPagination

    def get(self, request):
        class_name = request.query_params.get('class_enrolled')
        section = request.query_params.get('section')
        selected_date_str = request.query_params.get('date')

        if not class_name or not section:
            response = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message="Class and section are required.",
                data={}
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        all_mark = True
        if selected_date_str:
            try:
                selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            except ValueError:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="Invalid date format. Please provide date in YYYY-MM-DD format.",
                    data={}
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            selected_date = None

        students = StudentUser.objects.filter(
            class_enrolled=class_name, section=section, user__school_id=request.user.school_id
        )
        serializer = StudentListBySectionSerializer(students, many=True)

        if selected_date:
            attendance_records = StudentAttendence.objects.filter(date=selected_date, student__in=students)
            attendance_mapping = {attendance.student_id: {'date': attendance.date, 'mark_attendence': attendance.mark_attendence} for attendance in attendance_records}

            for student_data in serializer.data:
                student_id = student_data['id']
                if student_id in attendance_mapping:
                    attendance_data = attendance_mapping[student_id]
                    student_data['date'] = attendance_data['date']
                    student_data['mark_attendence'] = attendance_data['mark_attendence']
                else:
                    all_mark = False
                    student_data['date'] = selected_date
                    student_data['mark_attendence'] = None
        response ={
            'status': status.HTTP_200_OK,
            'message': "Student list fetched successfully.",
            'all_attendance_marked': all_mark,
            'data': serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)


class StudentAttendanceCreateView(APIView):
    """
    This class is created to marked_attendance of the student's.
    """
    permission_classes = [IsTeacherUser, IsInSameSchool]

    def post(self, request):
        data_str = request.data.get('data')  # Assuming data is sent as form-data with key 'data'

        try:
            data_json = json.loads(data_str)
        except json.JSONDecodeError:
            return Response("Invalid JSON format", status=status.HTTP_400_BAD_REQUEST)

        for item in data_json:
            serializer = StudentAttendanceCreateSerializer(data=item)
            if serializer.is_valid():
                student_id = item['id']
                date = item['date']
                mark_attendence = item['mark_attendence']
                student_user = get_object_or_404(StudentUser, id=student_id)

                # Create or update attendance record
                StudentAttendence.objects.update_or_create(
                    student=student_user,
                    date=date,
                    mark_attendence=mark_attendence
                )
            else:
                response = create_response_data(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=serializer.errors,
                    data={}
                )
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        response = create_response_data(
            status=status.HTTP_200_OK,
            message=AttendenceMarkedMessage.ATTENDENCE_MARKED_SUCCESSFULLY,
            data={}
        )
        return Response(response, status=status.HTTP_200_OK)


class AdminCurriculumList(APIView):
    """
    This class is used to fetch the list of the curriculum which is added by admin.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def get(self, request):
        try:
            data = Curriculum.objects.filter(school_id=request.user.school_id).values_list('curriculum_name', flat=True).distinct()
            curriculum = list(data)
            curriculum_list = {
                "curriculum_name": curriculum
            }
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=CurriculumMessage.CURRICULUM_LIST_MESSAGE,
                data=curriculum_list
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class AdminClassesList(APIView):
    """
    This class is used to fetch the list of the classes which is added by admin.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def get(self, request):
        try:
            curriculum = request.query_params.get("curriculum_name")
            data = Curriculum.objects.filter(curriculum_name=curriculum, school_id=request.user.school_id)
            serializer = AdminClassListSerializer(data, many=True)
            class_names = [item['select_class'] for item in serializer.data]
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=CurriculumMessage.CLASSES_LIST_MESSAGE,
                data=class_names
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class AdminOptionalSubjectList(APIView):
    """
    This class is used to fetch the list of the optional subject which is added by admin according to curriculum.
    """
    permission_classes = [IsAdminUser, IsInSameSchool]

    def get(self, request):
        try:
            curriculum = request.query_params.get("curriculum_name")
            classes = request.query_params.get("class_name")
            data = Curriculum.objects.get(curriculum_name=curriculum, select_class=classes, school_id=request.user.school_id)
            subject = Subjects.objects.filter(curriculum_id=data.id)
            serializer = AdminOptionalSubjectListSerializer(subject, many=True)
            optional_subj = [item['optional_subject'] for item in serializer.data]
            response_data = create_response_data(
                status=status.HTTP_200_OK,
                message=CurriculumMessage.SUBJECT_LIST_MESSAGE,
                data=optional_subj
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            response_data = create_response_data(
                status=status.HTTP_400_BAD_REQUEST,
                message=e.args[0],
                data={}
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
class StudentAttendanceView(generics.ListAPIView):
    serializer_class = StudentAttendanceSerializer
    permission_classes = [IsStudentUser]

    def get_queryset(self):
        student_user = self.request.user.studentuser
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')

        queryset = StudentAttendence.objects.filter(student=student_user)
        if year and month:
            queryset = queryset.filter(date__year=year, date__month=month)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        response_data = {
            "status": status.HTTP_200_OK,
            "message": AttendenceMarkedMessage.STUDENT_ATTENDANCE_FETCHED_SUCCESSFULLY,
            "data": serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)