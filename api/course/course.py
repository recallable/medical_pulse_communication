from fastapi import APIRouter, Path

from models import MedicalCourse
from models.schemas.course import MedicalCourseResponse, MedicalCourseRequest
from utils.response import APIResponse

course_router = APIRouter(prefix='/course')


@course_router.post('/course-list')
async def course_list(request: MedicalCourseRequest):
    query = MedicalCourse.all()

    id = request.id
    if id:
        query = query.filter(id__gt=request.id)
    if request.course_code:
        query = query.filter(course_code=request.course_code)
    if request.course_name:
        query = query.filter(course_name__icontains=request.course_name)
    if request.medical_department:
        query = query.filter(medical_department=request.medical_department)
    news_course = await query.order_by(request.order_by).limit(request.limit)

    news = [
        MedicalCourseResponse(
            id=course.id,
            course_code=course.course_code,
            course_name=course.course_name,
            medical_department=course.medical_department,
            applicable_title=course.applicable_title,
            qualification_req=course.qualification_req,
            compliance_record_no=course.compliance_record_no,
            difficulty_level=course.difficulty_level,
            class_hours=course.class_hours,
            credit=course.credit,
            price=course.price,
            sale_status=course.sale_status,
            valid_period_days=course.valid_period_days,
            refund_rule=course.refund_rule,
            course_desc=course.course_desc,
            status=course.status,
            creator_id=course.creator_id,
            created_time=course.created_time,
            updated_time=course.updated_time,
            ext_info=course.ext_info,
        )
        for course in news_course
    ]

    return APIResponse.success(data={'news': news})


@course_router.get('/course-detail/{id}')
async def course_detail(id: int = Path(..., description='课程ID')):
    if not id:
        return APIResponse.error(message='课程ID不能为空')
    
    course = await MedicalCourse.get(id=id)
    if not course:
        return APIResponse.error(message='课程不存在')
    
    course_detail = MedicalCourseResponse(
        id=course.id,
        course_code=course.course_code,
        course_name=course.course_name,
        medical_department=course.medical_department,
        applicable_title=course.applicable_title,
        qualification_req=course.qualification_req,
        compliance_record_no=course.compliance_record_no,
        difficulty_level=course.difficulty_level,
        class_hours=course.class_hours,
        credit=course.credit,
        price=course.price,
        sale_status=course.sale_status,
        valid_period_days=course.valid_period_days,
        refund_rule=course.refund_rule,
        course_desc=course.course_desc,
        status=course.status,
        creator_id=course.creator_id,
        created_time=course.created_time,
        updated_time=course.updated_time,
        ext_info=course.ext_info,
    )
    
    return APIResponse.success(course_detail)
