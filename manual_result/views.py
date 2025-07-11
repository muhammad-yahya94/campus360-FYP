# Standard library imports
import pandas as pd
import logging
# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import math
# Local app imports
from .forms import *
from .models import *

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from .utils import clean_excel_columns

from django.contrib import messages

logger = logging.getLogger(__name__)




@login_required
def upload_result(request):
    if request.method == 'POST':
        form = CourseAndExcelUploadForm(request.POST, request.FILES)

        if form.is_valid():
            course_title = form.cleaned_data['course_title']
            course_code = form.cleaned_data['course_code']
            credit_hour = form.cleaned_data['credit_hour']
            lab_work = form.cleaned_data.get('lab_work', 0)
            opt = form.cleaned_data['opt']
            session = form.cleaned_data['session']
            semester = form.cleaned_data['semester']

            # Check if the course already exists in the current user's semester
            if Course.objects.filter(course_code=course_code, Semester=semester).exists():
                messages.error(request, f"A course with code '{course_code}' already exists in this semester.")
                return redirect('upload_result')

            print(f"course: {course_title}, code: {course_code}, semester: {semester}, session: {session}, opt: {opt}")

            if isinstance(session, str):  # If session is passed as ID
                try:
                    session = YearSession.objects.get(id=session)
                except YearSession.DoesNotExist:
                    messages.error(request, "Invalid session ID.")
                    return redirect('upload_result')

            try:
                course, created = Course.objects.get_or_create(
                    course_code=course_code,
                    Semester=semester,
                    defaults={
                        'course_title': course_title,
                        'credit_hour': credit_hour,
                        'lab_work': lab_work,
                        'opt': opt,
                    }
                )

                if created:
                    print(f"Created new course: {course}")
                else:
                    print(f"Course already exists: {course}")

                # Save the course ID for error handling
                course_id = course.id
                print(f"Course ID {course_id} created.")

                file = form.cleaned_data['file']
                print("Reading Excel file...")

                # Clean columns in the file (dynamically detect header and trim spaces)
                df = clean_excel_columns(file)
                print("Columns in DataFrame:", df.columns.tolist())

                # Replace NaN values in the 'Student Status' column with 'Result Not Notified'
                df['student status'] = df['student status'].fillna('Result Not Notified')

                # Helper function to handle "Result Not Notified" and NaN values
                def safe_float(value):
                    try:
                        if pd.isna(value) or value in ['Result Not Notified', '']:
                            return 0.0
                        return float(value)
                    except (ValueError, TypeError):
                        return 0.0

                # Iterate through the rows of the dataframe and save results
                for index, row in df.iterrows():
                    try:
                        print(f"Processing row {index + 1}")
                        roll_no = str(row.get('roll#', 'N/A')).split('.')[0]
                        student_name = row.get('student name', 'N/A')
                        father_name = row.get('student father name', 'N/A')
                        cnic = row.get('student cnic', 'N/A')
                        session = row.get('session', 'N/A')
                        attempt = safe_float(row.get('attempt')) or 0

                        internal_marks = safe_float(row.get('internal marks (6)', 0.0))
                        mid_term_marks = safe_float(row.get('mid term marks (12)', 0.0))
                        final_term_marks = safe_float(row.get('final term marks (42)', 0.0))
                        practical_work = safe_float(row.get('practical work (0)', 0.0))
                        total_obtained_marks = safe_float(row.get('total obtain marks', 0.0))

                        # Handle percentage correctly
                        percentage_str = str(row.get('marks %age', '0%')).strip()
                        if '%' in percentage_str:
                            percentage = float(percentage_str.replace('%', '').strip())
                        else:
                            percentage = safe_float(percentage_str)

                        if percentage <= 1:
                            percentage *= 100

                        grade = row.get('grade', 'N/A')
                        status = row.get('student status', 'Result Not Notified')

                        # Save student result
                        StudentResult.objects.create(
                            roll_no=roll_no,
                            student_name=student_name,
                            father_name=father_name,
                            cnic=cnic,
                            session=session,
                            attempt=attempt,
                            internal_marks=internal_marks or 0.0,
                            mid_term_marks=mid_term_marks or 0.0,
                            final_term_marks=final_term_marks or 0.0,
                            practical_work=practical_work or 0.0,
                            total_obtained_marks=total_obtained_marks or 0.0,
                            percentage=percentage or 0.0,
                            grade=grade,
                            status=status,
                            course=course
                        )
                    except Exception as e:
                        print(f"Error processing row {index + 1}: {str(e)}")
                        try:
                            # Try to delete the course if an error occurs
                            Course.objects.filter(id=course_id).delete()
                            print(f"Course with ID {course_id} was deleted due to an error.")
                        except Exception as delete_error:
                            print(f"Error deleting course with ID {course_id}: {str(delete_error)}")
                        messages.error(request, f"Error processing row {index + 1}: {str(e)}")
                        continue

                # If the file processed successfully, show success message
                messages.success(request, "Course and student results uploaded successfully.")
                return redirect('upload_result')
            except Exception as e:
                # If there was an error during file processing, delete the course by matching the ID
                print(f"Error during file processing: {str(e)}")
                messages.error(request, f"An error occurred while processing the file: {str(e)}")
                try:
                    Course.objects.filter(id=course_id).delete()
                    print(f"Course with ID {course_id} was deleted due to an error.")
                except Exception as delete_error:
                    print(f"Error deleting course with ID {course_id}: {str(delete_error)}")
        else:
            messages.error(request, "There was an error with the form. Please check the data and try again.")
    else:
        form = CourseAndExcelUploadForm()

    return render(request, 'upload_result.html', {'form': form})





from django.http import JsonResponse
from .models import Semester

def get_semesters(request):
    print("Request received at get_semesters endpoint")  # Debug statement

    session_id = request.GET.get('session_id')
    print(f"Session ID received: {session_id}")  # Debug statement

    if not session_id:
        print("No Session ID provided")  # Debug statement
        return JsonResponse({'error': 'Session ID not provided'}, status=400)

    try:
        semesters = Semester.objects.filter(year_session_id=session_id).values('id', 'name')
        print(f"Semesters found: {list(semesters)}")  # Debug statement
        return JsonResponse({'semesters': list(semesters)})
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug statement
        return JsonResponse({'error': 'An error occurred while fetching semesters'}, status=500)


from collections import defaultdict
# @login_required
def Result(request):
    not_found_roll = None
    roll_no = request.GET.get('search', '').strip()
    session_id = request.GET.get('session_id', '').strip()

    print(f"Roll No: {roll_no}, Session ID: {session_id}")

    # year_session = YearSession.objects.filter(department=user)
    year_session = YearSession.objects.all()
    print(f"Year Session data fetched: {year_session.count()} entries.")

    # opt_courses = Course.objects.filter(opt=True, Semester__year_session__department=user)
    opt_courses = Course.objects.filter(opt=True)
    print(f"Optional courses fetched: {opt_courses.count()} entries.")

    results = StudentResult.objects.filter(
        roll_no=roll_no,
        # course__Semester__year_session__department=user
    )
    if roll_no:
        if not results:
            # print(f"no result found for this number : {roll_no}")
            not_found_roll = f"No result found for   {roll_no}"

    print(f"Initial results fetched: {results.count()} entries.")

    if session_id:
        results = results.filter(course__Semester__year_session__id=session_id)
        print(f"Results filtered by session_id. Total: {results.count()} entries.")

    if roll_no and session_id:
         if not results:
            # print(f"no result found for this number : {roll_no}")
            not_found_roll = f"No result found for   {roll_no}"

    opt_results = results.filter(course__in=opt_courses)
    results = results.exclude(course__in=opt_courses)

    print(f"Optional results count: {opt_results.count()}, Non-optional results count: {results.count()}.")

    def calculate_quality_points(result):
        credit_hour = result.course.credit_hour
        total_marks_float = float(result.percentage)
        total_marks = math.ceil(total_marks_float )
        print(f'this is float result -- {total_marks_float} --- total marks -- {total_marks}')
        quality_points_mapping = {
            40.0: 1.0, 41.0: 1.1, 42.0: 1.2, 43.0: 1.3, 44.0: 1.4, 45.0: 1.5,
            46.0: 1.6, 47.0: 1.7, 48.0: 1.8, 49.0: 1.9, 50.0: 2.0, 51.0: 2.07,
            52.0: 2.14, 53.0: 2.21, 54.0: 2.28, 55.0: 2.35, 56.0: 2.42, 57.0: 2.49,
            58.0: 2.56, 59.0: 2.63, 60.0: 2.70, 61.0: 2.76, 62.0: 2.82, 63.0: 2.88,
            64.0: 2.94, 65.0: 3.00, 66.0: 3.05, 67.0: 3.10, 68.0: 3.15, 69.0: 3.20,
            70.0: 3.25, 71.0: 3.30, 72.0: 3.35, 73.0: 3.40, 74.0: 3.45, 75.0: 3.50,
            76.0: 3.55, 77.0: 3.60, 78.0: 3.65, 79.0: 3.70, 80.0: 3.75, 81.0: 3.80,
            82.0: 3.85, 83.0: 3.90, 84.0: 3.95, 85.0: 4.0, 86.0: 4.0, 87.0: 4.0,
            88.0: 4.0, 89.0: 4.0, 90.0: 4.0, 91.0: 4.0, 92.0: 4.0, 93.0: 4.0,
            94.0: 4.0, 95.0: 4.0, 96.0: 4.0, 97.0: 4.0, 98.0: 4.0, 99.0: 4.0,
            100.0: 4.0
        }
        qp_p = quality_points_mapping.get(total_marks, 0.0) * credit_hour
        print(f"Result: {result.roll_no}, Marks: {total_marks}, Quality Points: {qp_p}")
        return round(qp_p, 2) if qp_p != 0 else 0.0

    # Log calculation details for each result
    for result in results:
        result.quality_points = calculate_quality_points(result)
        result.effective_credit_hour = (
            result.course.credit_hour if result.course.credit_hour and result.course.credit_hour > 0
            else result.course.lab_work or 0
        )
        result.course_marks = result.course.credit_hour * 20
        print(f"Result: {result.roll_no}, Quality Points: {result.quality_points}, Effective Credit Hours: {result.effective_credit_hour}, Course Marks: {result.course_marks}")

    excluded_courses = ['MTH-111', 'EXC456']
    filtered_results = [result for result in results if result.course.course_code not in excluded_courses]
    print(f"Filtered results count (excluding courses {excluded_courses}): {len(filtered_results)}.")

    t_q_points = sum([result.quality_points for result in filtered_results])
    total_quality_points = round(t_q_points, 2)
    all_credit_hours = sum([result.course.credit_hour for result in filtered_results])
    overall_gpa = round(total_quality_points / all_credit_hours, 2) if all_credit_hours > 0 else 0

    print(f"Total Quality Points: {total_quality_points}, Total Credit Hours: {all_credit_hours}, Overall GPA: {overall_gpa}")

    total_marks = sum([float(result.percentage) * result.course.credit_hour for result in filtered_results])
    avg_percentage = math.ceil((total_marks / all_credit_hours)) if all_credit_hours > 0 else 0
    print(f"Total Marks: {total_marks}, Average Percentage: {avg_percentage}")

    total_credit_hours = sum([result.course.credit_hour for result in results])
    max_marks = sum([result.total_obtained_marks for result in results])
    total_full_marks = sum([result.course.credit_hour * 20 for result in results])
    print(f"Total Credit Hours: {total_credit_hours}, Max Marks: {max_marks}, Total Full Marks: {total_full_marks}")

    semester_results = defaultdict(list)
    semester_gpas = {}
    semester_totals = {}

    for result in results:
        semester_results[result.course.Semester.name].append(result)

    # Calculate GPA, total credit hours, full marks, etc. for each semester
    for semester, semester_data in semester_results.items():
        total_qp = sum([calculate_quality_points(result) for result in semester_data])
        total_credit_hours = sum([result.course.credit_hour for result in semester_data])
        semester_gpas[semester] = round(total_qp / total_credit_hours, 2) if total_credit_hours > 0 else 0

        total_marks = sum([float(result.percentage) * result.course.credit_hour for result in semester_data])
        avg_percentage = math.ceil((total_marks / total_credit_hours)) if total_credit_hours > 0 else 0
        total_full_marks = sum([result.course.credit_hour * 20 for result in semester_data])
        max_marks = sum([result.total_obtained_marks for result in semester_data])
        total_quality_points = round(sum([calculate_quality_points(result) for result in semester_data]), 2)

        # Save the totals in a dictionary
        semester_totals[semester] = {
            'total_credit_hours': total_credit_hours,
            'total_full_marks': total_full_marks,
            'max_marks': max_marks,
            'average_percentage': avg_percentage,
            'total_quality_points': total_quality_points
        }

        # Print individual values for debugging
        print(f"Semester: {semester}")
        print(f"  Total Credit Hours: {total_credit_hours}")
        print(f"  Total Full Marks: {total_full_marks}")
        print(f"  Max Marks: {max_marks}")
        print(f"  Average Percentage: {avg_percentage}%")
        print(f"  Total Quality Points: {total_quality_points}")

    # You can still pass other context data to the template if needed, or just render without it.
    context = {
        'student': results.first(),
        'semester_results': dict(semester_results),
        'semester_gpas': semester_gpas,
        'opt_results': opt_results,
        'year_session': year_session,
        'roll_no': roll_no,
        'semester_totals': semester_totals,
        'msg':not_found_roll,




        "total_credit_hours":total_credit_hours,
        "total_full_marks":total_full_marks,
        "max_marks":max_marks,
        "avg_percentage":avg_percentage,
        "total_quality_points":total_quality_points,
    }
    pprint.pprint(context)
    # Render the template with the given context (you can omit 'semester_totals' from context if you don't want to pass it)
    return render(request, 'Result.html', context)

import pprint

