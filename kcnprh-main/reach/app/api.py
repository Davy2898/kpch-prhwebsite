import json
import os
from urllib import request as urlrequest
from urllib.parse import urlencode

import bleach
from flask import Blueprint, jsonify, request, url_for
from sqlalchemy import desc, or_

from . import db
from .models import Category, Comment, Page, Post

bp = Blueprint("api", __name__, url_prefix="/api")


def _asset(path: str) -> str:
    return url_for("static", filename=path)


def _date(value):
    if not value:
        return None
    return value.strftime("%d %b %Y")


def _excerpt(html: str | None, length: int = 180) -> str:
    text = bleach.clean(html or "", tags=[], strip=True)
    text = " ".join(text.split())
    return text if len(text) <= length else f"{text[:length].rstrip()}..."


def _post(post: Post, include_body: bool = False) -> dict:
    data = {
        "id": post.id,
        "title": post.PostTitle or "Untitled post",
        "excerpt": _excerpt(post.PostDetails),
        "date": _date(post.PostingDate),
        "views": post.viewCounter or 0,
        "image": _asset(f"uploads/{post.PostImage}") if post.PostImage else None,
        "url": f"/post/{post.id}",
        "category": None,
        "subcategory": None,
    }
    if post.category:
        data["category"] = {
            "id": post.category.id,
            "name": post.category.CategoryName,
            "url": f"/category/{post.category.id}",
        }
    if post.subcategory:
        data["subcategory"] = {
            "id": post.subcategory.SubCategoryId,
            "name": post.subcategory.Subcategory,
        }
    if include_body:
        data["body"] = post.PostDetails or ""
    return data


def _category(category: Category) -> dict:
    return {
        "id": category.id,
        "name": category.CategoryName,
        "description": category.Description,
        "url": f"/category/{category.id}",
    }


@bp.get("/site")
def site():
    return jsonify(
        {
            "name": "Kampong Chhnang Provincial Referral Hospital",
            "khmerName": "មន្ទីរពេទ្យខេត្តកំពង់ឆ្នាំង",
            "tagline": "Compassionate care for Kampong Chhnang families",
            "logo": _asset("img/logo.svg"),
            "heroImage": _asset("img/kampongchhnangentry.jpg"),
            "emergencyPhones": ["097 98 12 812", "097 79 75 111"],
            "stats": [
                {"label": "Service", "value": "24/7"},
                {"label": "Care Level", "value": "CPA3"},
                {"label": "From Phnom Penh", "value": "91 km"},
            ],
            "services": [
                {
                    "title": "Outpatient Care",
                    "khmer": "ពិគ្រោះ និងព្យាបាលជំងឺក្រៅ",
                    "image": _asset("img/opd.jpg"),
                    "details": {
                        "icon": "stethoscope",
                        "title": "ពិគ្រោះ និងព្យាបាលជំងឺក្រៅ",
                        "subtitle": "Outpatient Care",
                        "description": "ផ្តល់សេវាពិគ្រោះ ពិនិត្យ និងព្យាបាលជំងឺទូទៅ និងឯកទេសដោយវេជ្ជបណ្ឌិតជំនាញ ដោយមិនចាំបាច់គេងសម្រាកនៅមន្ទីរពេទ្យ។",
                        "english": "Comprehensive diagnostic and clinical consultation services tailored for non-admitted patients.",
                        "hours": "7:30 AM - 8:00 PM (Monday - Sunday)",
                        "specialties": "General Medicine, Pediatrics, Cardiology, OB-GYN",
                    },
                },
                {
                    "title": "Eye Care & Ophthalmology",
                    "khmer": "ព្យាបាល និងថែទាំភ្នែក",
                    "image": _asset("img/eyeopt.JPG"),
                    "details": {
                        "icon": "eye",
                        "iconLabel": "Eye / Vision Care",
                        "title": "ព្យាបាល និងថែទាំភ្នែក",
                        "subtitle": "Eye Care & Ophthalmology",
                        "description": "ផ្តល់សេវាពិនិត្យ វាស់កម្រិតគំហើញ ព្យាបាលជំងឺភ្នែកទូទៅ និងការវះកាត់កែតម្រូវដោយវេជ្ជបណ្ឌិតឯកទេសចក្ខុរោគ។",
                        "english": "Comprehensive vision exams, eye disease treatments, and advanced ophthalmic surgical care.",
                        "hours": "7:30 AM - 6:00 PM (Monday - Sunday)",
                        "keyServices": "Cataract Surgery, Glaucoma Care, Vision Testing, Pediatric Eye Care",
                    },
                },
                {
                    "title": "Emergency Ambulance 24/7",
                    "khmer": "រថយន្តសង្គ្រោះបន្ទាន់",
                    "image": _asset("img/car.jpg"),
                    "details": {
                        "icon": "ambulance",
                        "iconLabel": "Ambulance / Emergency Red Cross",
                        "title": "រថយន្តសង្គ្រោះបន្ទាន់",
                        "subtitle": "Emergency Ambulance 24/7",
                        "description": "ផ្តល់សេវារថយន្តសង្គ្រោះបន្ទាន់ និងសង្គ្រោះបឋម ២៤ ម៉ោងលើ ២៤ ម៉ោង ជាមួយឧបករណ៍វេជ្ជសាស្ត្រទំនើប និងក្រុមគ្រូពេទ្យសង្គ្រោះជំនាញ។",
                        "english": "24/7 rapid-response emergency medical transportation and advanced on-site life support services.",
                        "availability": "២៤ ម៉ោង / ៧ ថ្ងៃ (24 Hours / 7 Days)",
                        "hotline": "119 / 097 98 12 812",
                        "callNow": "097 98 12 812",
                        "callLabel": "ហៅរថយន្តសង្គ្រោះ (Call Now)",
                        "learnMoreLabel": "ស្វែងយល់បន្ថែម (Learn More)",
                    },
                },
                {
                    "title": "Emergency & ICU",
                    "khmer": "សេវាសង្គ្រោះបន្ទាន់ និងសង្គ្រោះបន្ទាន់កម្រិតធ្ងន់",
                    "image": _asset("img/ipdemr.jpg"),
                    "details": {
                        "icon": "heart-pulse",
                        "iconLabel": "Heart Pulse / Critical Care Bed",
                        "title": "សេវាសង្គ្រោះបន្ទាន់ និងសង្គ្រោះបន្ទាន់កម្រិតធ្ងន់",
                        "subtitle": "Emergency & ICU",
                        "description": "ផ្តល់ការសង្គ្រោះជីវិតបន្ទាន់ និងការថែទាំអ្នកជំងឺធ្ងន់ធ្ងរ ២៤ ម៉ោង ដោយបំពាក់ឧបករណ៍វេជ្ជសាស្ត្រជំនួយជីវិតកម្រិតខ្ពស់ និងក្រុមវេជ្ជបណ្ឌិតឯកទេស។",
                        "english": "24/7 critical intensive care and emergency resuscitation equipped with advanced life-support systems and specialized medical teams.",
                        "availability": "២៤ ម៉ោង / ៧ ថ្ងៃ (24 Hours / 7 Days)",
                        "units": "ICU (Intensive Care Unit), CCU (Cardiac Care), NICU/PICU (Neonatal/Pediatric)",
                        "callNow": "097 98 12 812",
                        "callLabel": "ទាក់ទងបន្ទាន់ (Emergency Call)",
                        "learnMoreLabel": "ស្វែងយល់បន្ថែម (Learn More)",
                    },
                },
                {
                    "title": "Inpatient Care / IPD",
                    "khmer": "សម្រាកព្យាបាលនៅមន្ទីរពេទ្យ",
                    "image": _asset("img/ipd.jpg"),
                    "details": {
                        "icon": "bed",
                        "iconLabel": "Hospital Bed / Room Care",
                        "title": "សម្រាកព្យាបាលនៅមន្ទីរពេទ្យ",
                        "subtitle": "Inpatient Care / IPD",
                        "description": "ផ្តល់ការស្នាក់នៅព្យាបាលប្រកបដោយផាសុកភាព សុវត្ថិភាព និងការថែទាំវេជ្ជសាស្ត្រយ៉ាងយកចិត្តទុកដាក់ ២៤ ម៉ោង ដោយក្រុមគ្រូពេទ្យ និងគិលានុបដ្ឋាយិកាជំនាញ។",
                        "english": "Comfortable accommodations and 24/7 round-the-clock inpatient nursing and multidisciplinary medical care.",
                        "careCoverage": "២៤ ម៉ោង / ៧ ថ្ងៃ (24/7 Nursing & Doctor Rounds)",
                        "roomTypes": "Standard Ward, Semi-Private, VIP Suite, Deluxe Room",
                        "appointmentLabel": "កក់បន្ទប់សម្រាក (Reserve Room)",
                        "actionIcon": "bed",
                    },
                },
                {
                    "title": "Maternity & Delivery Care",
                    "khmer": "សម្ភព និងសម្រាលកូន",
                    "image": _asset("img/pexels-jonathanborba-3259625.jpg"),
                    "details": {
                        "icon": "baby",
                        "iconLabel": "Mother & Baby / Maternity Cradle",
                        "title": "សម្ភព និងសម្រាលកូន",
                        "subtitle": "Maternity & Delivery Care",
                        "description": "ផ្តល់ការថែទាំសុខភាពមាតា និងទារកយ៉ាងកក់ក្តៅ និងមានសុវត្ថិភាពខ្ពស់ ចាប់តាំងពីការពិនិត្យផ្ទៃពោះ ការសម្រាលកូន (ធម្មជាតិ និងវះកាត់) រហូតដល់ការថែទាំក្រោយសម្រាល ដោយក្រុមវេជ្ជបណ្ឌិតសម្ភព និងឆ្មបជំនាញ។",
                        "english": "Safe, compassionate, and comprehensive maternity care from prenatal health checks to natural/C-section delivery and postpartum recovery.",
                        "coverage": "២៤ ម៉ោង / ៧ ថ្ងៃ (24/7 Delivery & Emergency Care)",
                        "deliveryTypes": "Natural Delivery, Painless Delivery (Epidural), C-Section (វះកាត់)",
                        "appointmentLabel": "កក់កញ្ចប់សម្រាល (Maternity Packages)",
                        "actionIcon": "baby",
                    },
                },
                {
                    "title": "Surgery & Operating Theater",
                    "khmer": "សេវាវះកាត់ទូទៅ និងឯកទេស",
                    "image": _asset("img/bo.JPG"),
                    "details": {
                        "icon": "scissors",
                        "iconLabel": "Scalpel / Operating Theater / Surgery Mask",
                        "title": "សេវាវះកាត់ទូទៅ និងឯកទេស",
                        "subtitle": "Surgery & Operating Theater",
                        "description": "ផ្តល់សេវាវះកាត់ទូទៅ វះកាត់ចោះកាត់ (Laparoscopic / Celioscopy) និងការវះកាត់ឯកទេសស្មុគស្មាញ ក្នុងបន្ទប់វះកាត់ស្តង់ដារអន្តរជាតិ (Cleanroom) បំពាក់ឧបករណ៍ទំនើប និងក្រុមវេជ្ជបណ្ឌិតវះកាត់-សណ្តំជំនាញ។",
                        "english": "Advanced general, laparoscopic, and specialized surgical procedures performed in sterile modern operating suites by expert surgical teams.",
                        "operatingTheaters": "២៤ ម៉ោង / ៧ ថ្ងៃ សម្រាប់ករណីសង្គ្រោះបន្ទាន់ (24/7 Emergency Surgery)",
                        "techniques": "Minimally Invasive / Laparoscopy, Open Surgery, Day Surgery",
                        "appointmentLabel": "ពិគ្រោះជាមួយវេជ្ជបណ្ឌិតវះកាត់ (Book Consultation)",
                        "actionIcon": "scissors",
                    },
                },
                {
                    "title": "More Services & Specialties",
                    "khmer": "សេវាផ្សេងៗ",
                    "image": _asset("img/service.png"),
                    "details": {
                        "icon": "medical-cross",
                        "iconLabel": "Medical Cross / Healthcare Services",
                        "title": "សេវាផ្សេងៗ",
                        "subtitle": "More Services & Specialties",
                        "description": "ផ្តល់សេវាពិនិត្យ ពិគ្រោះ ព្យាបាល និងថែទាំសុខភាពគ្រប់ជ្រុងជ្រោយលើផ្នែកឯកទេសជាច្រើន ដោយក្រុមវេជ្ជបណ្ឌិត និងអ្នកជំនាញវេជ្ជសាស្ត្រ។",
                        "english": "Comprehensive clinical departments, specialized consultations, diagnostic care, and support therapies.",
                        "departments": "ENT, Dental, Hemodialysis, Mental Health, Physiotherapy, STDs, HIV/PrEP",
                        "serviceAvailability": "ពិគ្រោះជំងឺក្រៅ និងសង្គ្រោះបន្ទាន់ (OPD Consultations & In-Hospital Care)",
                        "learnMoreLabel": "ស្វែងរកសេវាកម្ម (Explore All Services)",
                        "appointmentLabel": "កក់ការណាត់ជួប (Book Appointment)",
                    },
                },
            ],
            "leaders": [
                {
                    "name": "Dr. Tum Sambath",
                    "khmer": "លោកវេជ្ជបណ្ឌិត. ទុំ សម្បត្តិ",
                    "role": "Director",
                    "image": _asset("img/tumsabath.png"),
                },
                {
                    "name": "Dr. Sok Kong",
                    "khmer": "លោកវេជ្ជបណ្ឌិត. សុខ គង់",
                    "role": "Vice Director",
                    "image": _asset("img/sokkong.png"),
                },
                {
                    "name": "Dr. Vorn Theavy",
                    "khmer": "លោកវេជ្ជបណ្ឌិត. វន ធានវី",
                    "role": "Vice Director",
                    "image": _asset("img/vorntheavy.png"),
                },
                {
                    "name": "Dr. Hing Narath",
                    "khmer": "លោកស្រីវេជ្ជបណ្ឌិត. ហ៊ីង ណារ៉ាត់",
                    "role": "Vice Director",
                    "image": _asset("img/heingnarath.png"),
                },
                {
                    "name": "Dr. Ouk Molyvann",
                    "khmer": "លោកស្រីវេជ្ជបណ្ឌិត. អ៊ុក ម៉ូលីវណ្ណ",
                    "role": "Vice Director",
                    "image": _asset("img/oukmulyvann.jpg"),
                },
            ],
            "contact": {
                "address": "Road 5, Krong Kampong Chhnang, Cambodia",
                "email": "Kampongchhnangprovincialhospit@gmail.com",
                "phones": ["(855) 97 98 12 812", "(855) 97 79 75 111"],
                "hours": "24/7",
                "facebook": "https://www.facebook.com/share/1AdB33NBfz/?mibextid=wwXIfr",
                "telegram": "https://t.me/kcnprh2022",
                "map": "https://maps.app.goo.gl/tpQto9NJxoKUaD5d6",
            },
        }
    )


@bp.get("/posts")
def posts():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 30)
    category_id = request.args.get("category_id", type=int)
    qstr = (request.args.get("q") or "").strip()

    query = Post.query.filter(Post.Is_Active == 1)
    if category_id:
        query = query.filter(Post.CategoryId == category_id)
    if qstr:
        query = query.filter(or_(Post.PostTitle.ilike(f"%{qstr}%"), Post.PostDetails.ilike(f"%{qstr}%")))

    ordered = query.order_by(desc(Post.PostingDate))
    total = ordered.count()
    items = ordered.offset((page - 1) * per_page).limit(per_page).all()
    trending = Post.query.filter(Post.Is_Active == 1).order_by(desc(Post.viewCounter)).limit(8).all()
    categories = Category.query.order_by(Category.CategoryName).all()

    return jsonify(
        {
            "posts": [_post(item) for item in items],
            "trending": [_post(item) for item in trending],
            "categories": [_category(item) for item in categories],
            "pagination": {
                "page": page,
                "perPage": per_page,
                "total": total,
                "pages": max((total + per_page - 1) // per_page, 1),
                "hasPrev": page > 1,
                "hasNext": page * per_page < total,
            },
        }
    )


@bp.get("/posts/<int:post_id>")
def post_detail(post_id: int):
    post = Post.query.get_or_404(post_id)
    if not post.Is_Active:
        return jsonify({"message": "Not found"}), 404
    comments = Comment.query.filter_by(postId=post_id, status=1).order_by(desc(Comment.postingDate)).all()
    return jsonify(
        {
            "post": _post(post, include_body=True),
            "comments": [
                {
                    "id": comment.id,
                    "name": comment.name,
                    "comment": comment.comment,
                    "date": _date(comment.postingDate),
                }
                for comment in comments
            ],
        }
    )


@bp.get("/categories")
def categories():
    return jsonify({"categories": [_category(item) for item in Category.query.order_by(Category.CategoryName).all()]})


@bp.get("/pages/<string:slug>")
def page(slug: str):
    page_obj = Page.query.filter(Page.PageName == slug).first()
    if not page_obj:
        return jsonify({"message": "Not found"}), 404
    return jsonify(
        {
            "page": {
                "id": page_obj.id,
                "name": page_obj.PageName,
                "title": page_obj.PageTitle,
                "body": page_obj.Description,
                "date": _date(page_obj.PostingDate),
            }
        }
    )


@bp.post("/appointments")
def appointment():
    payload = request.get_json(silent=True) or request.form
    name = (payload.get("name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip()
    reason = (payload.get("reason") or payload.get("case") or "").strip()
    department = (payload.get("department") or payload.get("pidaddep") or "").strip()
    datetime_value = (payload.get("datetime") or "").strip()

    if not name or not phone or not reason or not datetime_value:
        return jsonify({"message": "Please provide name, phone, reason, and date/time."}), 400

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    notice = None
    if token and chat_id:
        try:
            lines = [
                "New Appointment Request",
                f"Name: {name}",
                f"Phone: {phone}",
                f"Email: {email or '-'}",
                f"Department: {department or '-'}",
                f"Reason: {reason}",
                f"DateTime: {datetime_value}",
            ]
            data = urlencode({"chat_id": chat_id, "text": "\n".join(lines), "disable_web_page_preview": True}).encode()
            req = urlrequest.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urlrequest.urlopen(req, timeout=8) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if body.get("ok") is not True:
                    notice = body.get("description") or "Telegram notification failed."
        except Exception:
            notice = "Appointment saved, but Telegram notification could not be sent."

    return jsonify({"message": "Appointment request received.", "notice": notice})
