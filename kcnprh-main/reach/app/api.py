import json
import os
from urllib import request as urlrequest
from urllib.parse import urlencode

import bleach
from flask import Blueprint, jsonify, request, url_for
from flask_wtf.csrf import generate_csrf
from sqlalchemy import desc, or_

from . import csrf, db, limiter
from .models import Category, Comment, Page, Post, get_visitor_count, increment_visitor_count

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
            "publicUrl": os.getenv("PUBLIC_URL") or "https://dylan-syntax-checklist-paragraph.trycloudflare.com",
            "visitorCount": get_visitor_count(),
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
                        "consultations": [
                            {
                                "title": "ការពិគ្រោះជំងឺទូទៅ និងឯកទេស (General & Specialist Consultations)",
                                "description": "ការពិនិត្យសុខភាពជាប្រចាំ ការពិនិត្យរាងកាយទូទៅ និងការធ្វើរោគវិនិច្ឆ័យដោយវេជ្ជបណ្ឌិតឯកទេស (ឧទាហរណ៍៖ ឯកទេសជំងឺបេះដូង កុមារ រោគស្ត្រី និងសម្ភព ព្រមទាំងសើស្បែក)។",
                            },
                            {
                                "title": "ការធ្វើរោគវិនិច្ឆ័យ និងតេស្តមន្ទីរពិសោធន៍ (Diagnostic & Lab Testing)",
                                "description": "ការពិនិត្យឈាម វិភាគទឹកនោម ការថតកាំរស្មីអ៊ិច (X-rays) អេកូសាស្ត្រ (Ultrasounds) ស្កេន CT scans និងការវាស់ចង្វាក់បេះដូង (ECG/EKG)។",
                            },
                            {
                                "title": "ការវះកាត់តូច និងនីតិវិធីព្យាបាលទូទៅ (Minor Surgical & Clinical Procedures)",
                                "description": "ការដេររបួស ការវះកាត់យកដុំសាច់តូចៗ ឬប្រជ្រុយ ការច្រិបសាច់ពិនិត្យ (Biopsy) និងការលាងផ្លាស់ប្តូរបង់រុំរបួសជាប្រចាំ។",
                            },
                            {
                                "title": "ការគ្រប់គ្រង និងតាមដានជំងឺរ៉ាំរ៉ៃ (Chronic Disease Management)",
                                "description": "ការណាត់ជួបតាមដានសុខភាពជាប្រចាំសម្រាប់ជំងឺរ៉ាំរ៉ៃ ដូចជា ជំងឺលើសសម្ពាធឈាម ទឹកនោមផ្អែម ហឺត ឬបញ្ហាក្រពេញទីរ៉ូអ៊ីត។",
                            },
                            {
                                "title": "ការថែទាំបង្ការ និងការពិនិត្យស្វែងរកជំងឺ (Preventative Care & Screening)",
                                "description": "ការចាក់វ៉ាក់សាំង កញ្ចប់ពិនិត្យសុខភាពទូទៅ ការពិនិត្យស្វែងរកជំងឺមហារីក និងការពិគ្រោះយោបល់ផ្នែកអាហារូបត្ថម្ភ។",
                            },
                            {
                                "title": "ការស្តារនីតិសម្បទា និងការព្យាបាលដោយចលនា (Rehabilitation & Therapy)",
                                "description": "សេវាព្យាបាលដោយចលនា (Physical therapy) ការព្យាបាលការងារ និងមុខងារប្រចាំថ្ងៃ (Occupational therapy) ព្រមទាំងការព្យាបាលការនិយាយស្តី (Speech therapy)។",
                            },
                        ],
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
                        "consultations": [
                            {
                                "title": "ការពិនិត្យភ្នែក និងវាស់កម្រិតគំហើញ (Comprehensive Eye & Vision Exams)",
                                "description": "ការវាស់កម្រិតគំហើញ ពិនិត្យបញ្ហាភ្នែក (ម្ញូប ភ្នែកមើលជិតមិនច្បាស់ ភ្នែកផ្កាភ្លើង) និងការកាត់វ៉ែនតា ឬកែវភ្នែក (Contact lenses)។",
                            },
                            {
                                "title": "ការធ្វើរោគវិនិច្ឆ័យ និងព្យាបាលជំងឺភ្នែក (Eye Disease Diagnosis & Management)",
                                "description": "ព្យាបាលជំងឺភ្នែកស្ងួត រលាកភ្នែក ជំងឺឡើងទឹកបាតភ្នែក (Glaucoma) ជំងឺភ្នែកឡើងបាយ (Cataract) និងជំងឺខូចរ៉េទីនដោយសារទឹកនោមផ្អែម (Diabetic Retinopathy)។",
                            },
                            {
                                "title": "ការពិនិត្យតាមម៉ាស៊ីនឯកទេសចក្ខុរោគ (Specialized Ophthalmic Diagnostics)",
                                "description": "ការពិនិត្យដោយម៉ាស៊ីនពង្រីកបាតភ្នែក (Slit Lamp) ការវាស់សម្ពាធទឹកក្នុងគ្រាប់ភ្នែក (Tonometry) និងការថតស្កេនស្រទាប់បាតភ្នែក (OCT)។",
                            },
                            {
                                "title": "ការវះកាត់ និងការព្យាបាលដោយកាំរស្មីឡាស៊ែរ (Surgical & Laser Procedures)",
                                "description": "ការវះកាត់ប្តូរកែវភ្នែកឡើងបាយ (Cataract Surgery) ការវះកាត់កន្ទុយថ្លែន ការបាញ់ឡាស៊ែរព្យាបាលបាតភ្នែក និងការវះកាត់កែសម្រួលត្របកភ្នែក។",
                            },
                            {
                                "title": "ការសង្គ្រោះបន្ទាន់ និងថែទាំភ្នែកកុមារ (Emergency & Pediatric Eye Care)",
                                "description": "ការយកកម្ទេចកំទី ឬធូលីចេញពីភ្នែក ការព្យាបាលភ្នែកប៉ះទង្គិច ឬសារធាតុគីមី និងការពិនិត្យព្យាបាលភ្នែកស្រលៀង ឬភ្នែកខ្ជិល (Amblyopia) ចំពោះកុមារ។",
                            },
                        ],
                    },
                },
                {
                    "title": "Ear, Nose & Throat (ENT)",
                    "khmer": "សេវា ពិនិត្យត្រចៀក ច្រមុះ បំពង់ក",
                    "image": _asset("img/opt.jpg"),
                    "details": {
                        "icon": "medical-cross",
                        "iconLabel": "Ear, Nose & Throat / ENT",
                        "title": "សេវា ពិនិត្យត្រចៀក ច្រមុះ បំពង់ក",
                        "subtitle": "Ear, Nose & Throat (ENT)",
                        "description": "ផ្តល់សេវាពិនិត្យ ពិគ្រោះ និងព្យាបាលបញ្ហាត្រចៀក ច្រមុះ បំពង់ក និងផ្លូវដង្ហើមផ្នែកខាងលើ។",
                        "english": "ENT consultation for ear, nose, throat, sinus, hearing, and upper airway concerns.",
                        "hours": "7:30 AM - 5:00 PM (Monday - Sunday)",
                        "keyServices": "Ear Exams, Nasal & Sinus Care, Throat Consultation, Hearing Concerns",
                        "consultations": [
                            {
                                "title": "ពិនិត្យត្រចៀក និងបញ្ហាការស្តាប់ (Ear & Hearing Check)",
                                "description": "ពិនិត្យការឈឺត្រចៀក ស្ទះត្រចៀក ហូរទឹកត្រចៀក សំឡេងរោទ៍ក្នុងត្រចៀក និងបញ្ហាការស្តាប់។",
                            },
                            {
                                "title": "ពិនិត្យច្រមុះ និងរលាកស៊ីនុស (Nose & Sinus Care)",
                                "description": "ពិគ្រោះបញ្ហាតឹងច្រមុះ រលាកច្រមុះ អាលែកហ្ស៊ី ឈាមច្រមុះ និងរលាកស៊ីនុស។",
                            },
                            {
                                "title": "ពិនិត្យបំពង់ក និងសម្លេង (Throat & Voice Care)",
                                "description": "ពិនិត្យឈឺបំពង់ក ក្អករ៉ាំរ៉ៃ ស្អកសំឡេង រលាកក្រពេញ tonsil និងបញ្ហាលេប។",
                            },
                        ],
                        "appointmentLabel": "កក់ការណាត់ជួប ENT (Book ENT Visit)",
                    },
                },
                {
                    "title": "Pediatric & Neonatal Care",
                    "khmer": "ផ្នែកជំងឺកុមារ-ទារក",
                    "image": _asset("img/pdt.png"),
                    "details": {
                        "icon": "baby",
                        "iconLabel": "Baby / Pediatric & Neonatal Care",
                        "title": "ផ្នែកជំងឺកុមារ-ទារក",
                        "subtitle": "Pediatric & Neonatal Care",
                        "description": "ផ្តល់សេវាពិនិត្យ ពិគ្រោះ ព្យាបាល និងតាមដានសុខភាពកុមារ ទារក និងទារកទើបនឹងកើត។",
                        "english": "Pediatric and neonatal care for children, infants, and newborns, including consultation, treatment, and follow-up.",
                        "hours": "7:30 AM - 5:00 PM (Monday - Sunday)",
                        "keyServices": "Child Consultation, Newborn Care, Vaccination Advice, Growth Monitoring",
                        "consultations": [
                            {
                                "title": "ពិនិត្យ និងព្យាបាលជំងឺកុមារ (Pediatric Consultation)",
                                "description": "ពិគ្រោះ ពិនិត្យ និងព្យាបាលបញ្ហាសុខភាពកុមារទូទៅ ដូចជា ក្តៅខ្លួន ក្អក រាគ អាឡែកហ្ស៊ី និងជំងឺឆ្លងទូទៅ។",
                            },
                            {
                                "title": "ថែទាំទារក និងទារកទើបនឹងកើត (Newborn & Neonatal Care)",
                                "description": "តាមដានសុខភាពទារក ការបំបៅដោះ ការលូតលាស់ ទម្ងន់ និងសញ្ញាដែលត្រូវយកចិត្តទុកដាក់ក្រោយសម្រាល។",
                            },
                            {
                                "title": "តាមដានការលូតលាស់ និងការចាក់វ៉ាក់សាំង (Growth & Vaccination Guidance)",
                                "description": "ផ្តល់ការណែនាំអំពីកាលវិភាគវ៉ាក់សាំង អាហារូបត្ថម្ភ ការលូតលាស់ និងការថែទាំកុមារតាមវ័យ។",
                            },
                        ],
                        "appointmentLabel": "កក់ការណាត់ជួបកុមារ-ទារក (Book Pediatric Visit)",
                        "actionIcon": "baby",
                    },
                },
                {
                    "title": "Hemodialysis Service",
                    "khmer": "សេវា លាងឈាម",
                    "image": _asset("img/dialysis.png"),
                    "details": {
                        "icon": "heart-pulse",
                        "iconLabel": "Dialysis / Kidney Care",
                        "title": "សេវា លាងឈាម",
                        "subtitle": "Hemodialysis Service",
                        "description": "ផ្តល់សេវាលាងឈាមសម្រាប់អ្នកជំងឺខ្សោយតម្រងនោម ដោយមានការតាមដានសុវត្ថិភាព និងការថែទាំដោយក្រុមវេជ្ជសាស្ត្រ។",
                        "english": "Hemodialysis support for patients with kidney failure, with careful monitoring and clinical care.",
                        "hours": "7:30 AM - 5:00 PM (Monday - Sunday)",
                        "keyServices": "Hemodialysis, Kidney Failure Support, Patient Monitoring, Clinical Follow-up",
                        "consultations": [
                            {
                                "title": "សេវាលាងឈាម (Hemodialysis Treatment)",
                                "description": "ផ្តល់ការលាងឈាមតាមវេជ្ជបញ្ជាសម្រាប់អ្នកជំងឺខ្សោយតម្រងនោមរ៉ាំរ៉ៃ ឬត្រូវការការព្យាបាលបន្ត។",
                            },
                            {
                                "title": "តាមដានសញ្ញាជីវិត និងសុវត្ថិភាព (Monitoring & Safety)",
                                "description": "តាមដានសម្ពាធឈាម សញ្ញាជីវិត និងស្ថានភាពអ្នកជំងឺក្នុងអំឡុងពេលលាងឈាម។",
                            },
                            {
                                "title": "ពិគ្រោះ និងណែនាំការថែទាំ (Consultation & Care Guidance)",
                                "description": "ផ្តល់ការណែនាំអំពីការថែទាំសុខភាព ការបន្តព្យាបាល និងការណាត់ជួបតាមដានជាមួយវេជ្ជបណ្ឌិត។",
                            },
                        ],
                        "appointmentLabel": "កក់ការណាត់ជួបលាងឈាម (Book Hemodialysis Visit)",
                    },
                },
                {
                    "title": "Emergency Ambulance 24/7",
                    "khmer": "រថយន្តសង្គ្រោះបន្ទាន់",
                    "image": _asset("img/car.jpg"),
                    "details": {
                        "icon": "ambulance",
                        "iconLabel": "Ambulance / Emergency Red Cross",
                        "title": "សេវាសង្គ្រោះបន្ទាន់ និងបញ្ជូនអ្នកជំងឺ ២៤/៧",
                        "subtitle": "24/7 Rapid Emergency Response & Transfer",
                        "description": "ផ្តល់ការឆ្លើយតបបន្ទាន់ក្នុងការចុះទទួលអ្នកជំងឺដល់គេហដ្ឋាន កន្លែងកើតហេតុ ឬគ្រោះថ្នាក់ចរាចរណ៍ ២៤ម៉ោងលើ២៤ម៉ោង ដោយសុវត្ថិភាព និងទាន់ពេលវេលា។",
                        "english": "Emergency Ambulance 24/7",
                        "availability": "២៤ ម៉ោង / ៧ ថ្ងៃ (24 Hours / 7 Days)",
                        "hotline": "119 / 097 98 12 812",
                        "callNow": "097 98 12 812",
                        "callLabel": "ហៅរថយន្តសង្គ្រោះ (Call Now)",
                        "learnMoreLabel": "ស្វែងយល់បន្ថែម (Learn More)",
                        "consultations": [
                            {
                                "title": "បរិក្ខារទ្រទ្រង់ជីវិតកម្រិតធ្ងន់ចល័ត (Advanced Life Support & Mobile ICU)",
                                "description": "រថយន្តបំពាក់ដោយម៉ាស៊ីនជំនួយដង្ហើម (Ventilator/CPAP) ម៉ាស៊ីនឆក់បេះដូង (Defibrillator/AED) ម៉ូនីទ័រតាមដានសញ្ញាជីវិត (Vital Signs Monitor) និងធុងអុកស៊ីសែនវេជ្ជសាស្ត្រស្តង់ដារ។",
                            },
                            {
                                "title": "ក្រុមគ្រូពេទ្យ និងគិលានុបដ្ឋាកសង្គ្រោះបន្ទាន់ (Specialized Paramedic & Medical Team)",
                                "description": "មានវត្តមានវេជ្ជបណ្ឌិត និងគិលានុបដ្ឋាកជំនាញសង្គ្រោះបឋមផ្ទាល់នៅលើរថយន្ត ដើម្បីផ្តល់ការព្យាបាលសង្គ្រោះបន្ទាន់ភ្លាមៗក្នុងពេលធ្វើដំណើរ។",
                            },
                            {
                                "title": "សេវាផ្ទេរ និងបញ្ជូនអ្នកជំងឺអន្តរមន្ទីរពេទ្យ (Inter-Hospital & Cross-Province Referral)",
                                "description": "សេវាបញ្ជូនអ្នកជំងឺសម្រាកព្យាបាលបន្តរវាងមន្ទីរពេទ្យ និងមន្ទីរពេទ្យ ទូទាំងរាជធានី-ខេត្ត ឬបញ្ជូនបន្តទៅកាន់ព្រំដែន និងជើងហោះហើរវេជ្ជសាស្ត្រ (Medevac)។",
                            },
                            {
                                "title": "សេវារថយន្តសង្គ្រោះប្រចាំការក្នុងព្រឹត្តិការណ៍ (Event Standby & Medical Coverage)",
                                "description": "ផ្តល់សេវារថយន្តសង្គ្រោះ និងក្រុមបុគ្គលិកសុខាភិបាលប្រចាំការសម្រាប់ការប្រគំតន្ត្រី ការប្រកួតកីឡា កិច្ចប្រជុំ ឬកម្មវិធីសាធារណៈធំៗ។",
                            },
                        ],
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
                        "consultations": [
                            {
                                "title": "សេវាសង្គ្រោះបន្ទាន់ ២៤ម៉ោង (24/7 Emergency Medical Care)",
                                "description": "ផ្តល់ការពិនិត្យ ធ្វើរោគវិនិច្ឆ័យ និងព្យាបាលបន្ទាន់ចំពោះករណីគ្រោះថ្នាក់ចរាចរណ៍ របួសធ្ងន់ធ្ងរ ឬស្ថានភាពជំងឺដែលគំរាមកំហែងដល់អាយុជីវិតភ្លាមៗ។",
                            },
                            {
                                "title": "ការសង្គ្រោះបន្ទាន់ផ្នែកបេះដូង និងសរសៃឈាម (Cardiac & Stroke Emergency)",
                                "description": "ការអន្តរាគមន៍រហ័សទាន់ពេលចំពោះជំងឺគាំងបេះដូង (Myocardial Infarction) ដាច់សរសៃឈាមខួរក្បាល (Stroke) និងចង្វាក់បេះដូងលោតខុសប្រក្រតីធ្ងន់ធ្ងរ។",
                            },
                            {
                                "title": "បន្ទប់សង្គ្រោះបន្ទាន់កម្រិតធ្ងន់ និងប្រព័ន្ធជំនួយដង្ហើម (Intensive Care Unit & Mechanical Ventilation)",
                                "description": "បំពាក់ប្រព័ន្ធម៉ាស៊ីនជំនួយដង្ហើមកម្រិតខ្ពស់ (ICU Ventilators) ម៉ាស៊ីនបូមស្លេស្ម និងការតាមដានសញ្ញាជីវិតជាបន្តបន្ទាប់ ២៤/៧ ដោយប្រព័ន្ធឌីជីថល (Hemodynamic Monitoring)។",
                            },
                            {
                                "title": "ការគ្រប់គ្រងការឆ្លងមេរោគក្នុងឈាមធ្ងន់ធ្ងរ និងការដួលសន្លប់ (Sepsis & Shock Management)",
                                "description": "ការធ្វើរោគវិនិច្ឆ័យរហ័ស ផ្តល់ថ្នាំ និងសារធាតុរាវតាមសរសៃឈាមដើម្បីទប់ទល់នឹងស្ថានភាពឆ្លងមេរោគចូលចរន្តឈាមធ្ងន់ធ្ងរ និងសម្ពាធឈាមធ្លាក់ចុះខ្លាំង។",
                            },
                            {
                                "title": "ការថែទាំយ៉ាងយកចិត្តទុកដាក់បន្ទាប់ពីការវះកាត់ធំៗ (Post-Surgical Critical Care)",
                                "description": "ការតាមដាន និងថែទាំអ្នកជំងឺក្រោយការវះកាត់ធំៗ ដើម្បីទប់ស្កាត់ផលវិបាក និងជួយឱ្យអ្នកជំងឺឆាប់ដឹងខ្លួន និងមានសុវត្ថិភាពខ្ពស់។",
                            },
                        ],
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
                        "consultations": [
                            {
                                "title": "បន្ទប់សម្រាកព្យាបាលចម្រុះ និងឯកជន (Standard & VIP Patient Rooms)",
                                "description": "ជម្រើសបន្ទប់ទូលាយ មានអនាម័យខ្ពស់ បំពាក់គ្រែពេទ្យស្វ័យប្រវត្តិ ម៉ាស៊ីនត្រជាក់ ទូរទស្សន៍ ប្រព័ន្ធហៅគិលានុបដ្ឋាកបន្ទាន់ (Nurse Call System) និងបន្ទប់ទឹកស្អាតដាច់ដោយឡែក។",
                            },
                            {
                                "title": "ការតាមដានសុខភាព និងសញ្ញាជីវិត ២៤/៧ (Round-the-Clock Clinical Monitoring)",
                                "description": "ក្រុមគិលានុបដ្ឋាក និងវេជ្ជបណ្ឌិតប្រចាំការតាមដានសញ្ញាជីវិត ការផ្តល់ថ្នាំ និងការចាក់សេរ៉ូមតាមវេជ្ជបញ្ជាយ៉ាងត្រឹមត្រូវ និងទៀងទាត់ពេញមួយថ្ងៃ និងមួយយប់។",
                            },
                            {
                                "title": "ការថែទាំអ្នកជំងឺក្រោយការវះកាត់ (Post-Operative Recovery Care)",
                                "description": "ការគ្រប់គ្រងការឈឺចាប់ ការសម្អាត និងផ្លាស់ប្តូរបង់របួសដោយបច្ចេកទេសគ្មានមេរោគ (Aseptic Technique) និងការជួយស្តារនីតិសម្បទាឱ្យឆាប់ជាសះស្បើយឡើងវិញ។",
                            },
                            {
                                "title": "សេវាអាហារូបត្ថម្ភវេជ្ជសាស្ត្រសម្រាប់អ្នកជំងឺ (Clinical Nutrition & Dietetic Support)",
                                "description": "ការរៀបចំរបបអាហារមានអនាម័យ និងត្រឹមត្រូវតាមលក្ខខណ្ឌជំងឺជាក់ស្តែងរបស់អ្នកជំងឺម្នាក់ៗ (ដូចជា របបអាហារអ្នកជំងឺទឹកនោមផ្អែម លើសឈាម ឬក្រោយវះកាត់)។",
                            },
                            {
                                "title": "សេវាពិគ្រោះជំងឺដោយវេជ្ជបណ្ឌិតឯកទេសចម្រុះ (Multidisciplinary Specialist Rounds)",
                                "description": "ការចុះពិនិត្យតាមដានស្ថានភាពជំងឺផ្ទាល់ជារៀងរាល់ថ្ងៃដោយវេជ្ជបណ្ឌិតជំនាញឯកទេសចម្រុះ ដើម្បីវាយតម្លៃ និងកែសម្រួលផែនការព្យាបាលឱ្យកាន់តែមានប្រសិទ្ធភាព។",
                            },
                        ],
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
                        "consultations": [
                            {
                                "title": "ការតាមដានសុខភាពគភ៌មុនពេលសម្រាល (Comprehensive Antenatal Care - ANC)",
                                "description": "ពិនិត្យសុខភាពម្តាយ និងការលូតលាស់របស់ទារកក្នុងផ្ទៃ អេកូសាស្ត្រ 4D/5D ពិនិត្យឈាមស្វែងរកភាពមិនប្រក្រតីនៃហ្សែន និងចាក់វ៉ាក់សាំងការពារជំងឺចាំបាច់សម្រាប់ស្ត្រីមានផ្ទៃពោះ។",
                            },
                            {
                                "title": "សេវាសម្រាលកូនតាមបែបធម្មជាតិ (Natural Labor & Normal Delivery)",
                                "description": "ការសម្រាលកូនតាមផ្លូវធម្មជាតិប្រកបដោយផាសុកភាព ភាពកក់ក្តៅ និងសុវត្ថិភាព ក្រោមការមើលថែដិតដល់ពីឆ្មបជំនាញ រួមជាមួយជម្រើសសម្រាលមិនឈឺចាប់ (Painless Delivery/Epidural)។",
                            },
                            {
                                "title": "ការសម្រាលកូនដោយការវះកាត់ (Cesarean Section - C-Section)",
                                "description": "បន្ទប់វះកាត់ស្តង់ដារបច្ចេកទេសទំនើប និងគ្មានមេរោគ ជាមួយក្រុមវេជ្ជបណ្ឌិតវះកាត់សម្ភព និងវេជ្ជបណ្ឌិតឯកទេសសណ្តំ សម្រាប់ករណីសម្រាលបន្ទាន់ ឬករណីគភ៌ពិបាកសម្រាល។",
                            },
                            {
                                "title": "ការថែទាំ និងសង្គ្រោះទារកទើបនឹងកើត (Neonatal Care & NICU)",
                                "description": "ការពិនិត្យសុខភាពទារកភ្លាមៗក្រោយកើត បរិក្ខារកម្ដៅទារក និងមានផ្នែកសង្គ្រោះទារកទើបនឹងកើតកម្រិតធ្ងន់ (NICU) ត្រៀមរួចជាស្រេចសម្រាប់ករណីទារកកើតមិនគ្រប់ខែ ឬមានបញ្ហាដង្ហើម។",
                            },
                            {
                                "title": "ការថែទាំមាតា និងទារកក្រោយពេលសម្រាល (Postnatal & Newborn Care)",
                                "description": "ការតាមដានសុខភាពស្បូន និងមុខរបួសម្តាយ ការណែនាំអំពីការបំបៅដោះកូនដោយទឹកដោះម្តាយ និងការចាក់វ៉ាក់សាំងការពារជំងឺដំបូងដល់ទារកទើបកើត។",
                            },
                        ],
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
                        "consultations": [
                            {
                                "title": "ការវះកាត់ចោះដោយម៉ាស៊ីនទំនើប (Laparoscopic & Minimally Invasive Surgery)",
                                "description": "ការវះកាត់ចោះខ្នាតតូច ដូចជាការវះកាត់ខ្នែងពោះវៀន ថង់ប្រមាត់ និងដុំសាច់ ដែលកាត់បន្ថយការឈឺចាប់ ស្លាកស្នាមតូច មិនបាត់បង់ឈាមច្រើន និងឆាប់បានចេញទៅផ្ទះវិញ។",
                            },
                            {
                                "title": "ការវះកាត់ទូទៅ និងប្រព័ន្ធរំលាយអាហារ (General & Gastrointestinal Surgery)",
                                "description": "ការព្យាបាលវះកាត់ជំងឺក្លន (Hernia) ដុំសាច់លើស្បែក និងជាលិកា ការវះកាត់ក្រពះ ពោះវៀនធំ និងជំងឺឫសដូងបាតដោយបច្ចេកវិទ្យាទំនើប។",
                            },
                            {
                                "title": "ការវះកាត់ឯកទេសឆ្អឹង និងសន្លាក់ (Orthopedic & Trauma Surgery)",
                                "description": "ការវះកាត់តឆ្អឹងបាក់ដោយគ្រោះថ្នាក់ ការព្យាបាលការរងរបួសសន្លាក់ សរសៃពួរ និងការវះកាត់ផ្លាស់ប្តូរសន្លាក់សិប្បនិម្មិត។",
                            },
                            {
                                "title": "បន្ទប់វះកាត់ស្តង់ដារអន្តរជាតិ និងប្រព័ន្ធសណ្តំទំនើប (Standard Operating Suites & Anesthesia Care)",
                                "description": "បំពាក់ម៉ាស៊ីនសណ្តំកម្រិតខ្ពស់ ឧបករណ៍ត្រួតពិនិត្យសញ្ញាជីវិតច្បាស់លាស់ និងប្រព័ន្ធគ្រប់គ្រងការឆ្លងរោគយ៉ាងតឹងរ៉ឹងបំផុតអំឡុងពេលវះកាត់។",
                            },
                            {
                                "title": "ការតាមដាន និងថែទាំក្នុងបន្ទប់ដាស់ (Post-Anesthesia Care Unit - PACU)",
                                "description": "ការមើលថែដិតដល់ភ្លាមៗក្រោយពេលវះកាត់រួច គ្រប់គ្រងការឈឺចាប់ និងតាមដានការដឹងខ្លួនឡើងវិញរបស់អ្នកជំងឺឱ្យមានស្ថិរភាពមុនពេលបញ្ជូនទៅបន្ទប់សម្រាក។",
                            },
                        ],
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
                        "departments": "Emergency, Inpatient, Outpatient, Laboratory, Blood Bank, X-Ray, Echography",
                        "serviceAvailability": "សម្រាកព្យាបាល ២៤ម៉ោង ពិគ្រោះព្យាបាល និងសេវាអមវេជ្ជសាស្ត្រ (24/7 Inpatient, Outpatient & Support Services)",
                        "consultations": [
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: រថយន្តគិលានសង្គ្រោះ (Ambulance)",
                                "description": "សេវាដឹកជញ្ជូន និងសង្គ្រោះបន្ទាន់ចល័ត ២៤ម៉ោង។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: សង្គ្រោះបន្ទាន់ (Emergency)",
                                "description": "ការទទួលពិនិត្យ និងសង្គ្រោះអ្នកជំងឺបន្ទាន់ទាន់ពេលវេលា។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: របួសវះកាត់ (Surgery-Trauma)",
                                "description": "សេវាសង្គ្រោះរបួសធ្ងន់ធ្ងរ និងការវះកាត់បន្ទាន់។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: ជំងឺទូទៅ (General Medicine)",
                                "description": "ការពិនិត្យ និងសម្រាកព្យាបាលជំងឺទូទៅ ២៤ម៉ោង។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: ប្រពោធនកម្ម (Intensive Care)",
                                "description": "ការសង្គ្រោះ និងថែទាំអ្នកជំងឺធ្ងន់ធ្ងរកម្រិតខ្ពស់ (ICU)។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: សម្ភព-រោគស្ត្រី (Gyneco-Maternity)",
                                "description": "សេវាសម្រាលកូន និងសង្គ្រោះបន្ទាន់ផ្នែកសម្ភព និងរោគស្ត្រី។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: ជំងឺកុមារ-ទារក (Paediatric-Neonate)",
                                "description": "ការថែទាំ និងសង្គ្រោះបន្ទាន់ជំងឺកុមារ និងទារកទើបនឹងកើត។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: ជំងឺរបេង (Tuberculosis)",
                                "description": "ការទទួល និងថែទាំអ្នកជំងឺរបេងសម្រាកពេទ្យ ២៤ម៉ោង។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: ចក្ខុរោគ (Ophtalmology)",
                                "description": "សេវាសង្គ្រោះ និងព្យាបាលបញ្ហាភ្នែកបន្ទាន់។",
                            },
                            {
                                "title": "សេវាសម្រាកព្យាបាល ២៤ម៉ោង: បន្ទប់ដាក់ដាច់ដោយឡែក (Isolation Room)",
                                "description": "បន្ទប់សម្រាកព្យាបាលដាច់ដោយឡែកសម្រាប់ជំងឺឆ្លងកម្រិតខ្ពស់។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: ជំងឺទូទៅ (General Medicine)",
                                "description": "ពិគ្រោះ និងព្យាបាលជំងឺទូទៅសម្រាប់មនុស្សពេញវ័យ។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: របួសវះកាត់ (Surgery-Trauma)",
                                "description": "ពិនិត្យ ព្យាបាលរបួស លាងរបួស និងពិគ្រោះជំងឺវះកាត់។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: ជំងឺកុមារ (Pediatric)",
                                "description": "ពិគ្រោះ ពិនិត្យសុខភាព និងព្យាបាលជំងឺកុមារគ្រប់វ័យ។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: សម្ភព-រោគស្ត្រី (Gyneco-Maternity)",
                                "description": "ពិនិត្យផ្ទៃពោះ ពិគ្រោះបញ្ហារោគស្ត្រី និងសុខភាពមាតា។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: ទឹកនោមផ្អែម-ឡើងសម្ពាធឈាម (Non Communicable Disease)",
                                "description": "ពិនិត្យ តាមដាន និងបើកថ្នាំជំងឺទឹកនោមផ្អែម លើសឈាម និងជំងឺមិនឆ្លងរ៉ាំរ៉ៃ។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: សេវាលាងឈាម (Hemodialysis)",
                                "description": "សេវាលាងឈាមសម្រាប់អ្នកជំងឺខ្សោយតម្រងនោមរ៉ាំរ៉ៃ និងស្រួចស្រាវ។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: ត្រចៀក ច្រមុះ បំពង់ក (E.N.T)",
                                "description": "ពិនិត្យ និងព្យាបាលជំងឺត្រចៀក ច្រមុះ បំពង់ក និងផ្លូវដង្ហើមផ្នែកខាងលើ។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: ជំងឺរបេង (Tuberculosis)",
                                "description": "ពិគ្រោះ ពិនិត្យស្លេស្ម តាមដាន និងបើកថ្នាំព្យាបាលជំងឺរបេង។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: ព្យាបាលដោយចលនា (Physiotherapy)",
                                "description": "សេវាស្តារនីតិសម្បទា និងកាយវប្បកម្មព្យាបាលដោយចលនា។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: សេវាព្យាបាលបន្ត (OI/ART)",
                                "description": "សេវាពិគ្រោះ តាមដានសុខភាព និងបើកថ្នាំប្រឆាំងមេរោគអេដស៍។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: សុខភាពផ្លូវចិត្ត (Mental Health)",
                                "description": "សេវាប្រឹក្សាយោបល់ និងព្យាបាលបញ្ហាសុខភាពផ្លូវចិត្ត និងអារម្មណ៍។",
                            },
                            {
                                "title": "សេវាពិគ្រោះព្យាបាល: សុខភាពគ្រួសារ (S.T.D)",
                                "description": "ពិនិត្យ ព្យាបាលជំងឺកាមរោគ និងផ្តល់ការប្រឹក្សាផែនការគ្រួសារ។",
                            },
                            {
                                "title": "សេវាអមវេជ្ជសាស្ត្រ និងជំនួយ: មន្ទីរពិសោធន៍លំដាប់ផ្កាយ៣ (Laboratory - 3-Star Level)",
                                "description": "សេវាវិភាគឈាម ទឹកនោម និងជីវគីមីវេជ្ជសាស្ត្រស្តង់ដារគុណភាពផ្កាយ៣។",
                            },
                            {
                                "title": "សេវាអមវេជ្ជសាស្ត្រ និងជំនួយ: សេវាផ្តល់ឈាម (Blood Bank)",
                                "description": "ធនាគារឈាមស្តុកទុក និងផ្តល់ឈាមសុវត្ថិភាពសម្រាប់សង្គ្រោះបន្ទាន់។",
                            },
                            {
                                "title": "សេវាអមវេជ្ជសាស្ត្រ និងជំនួយ: វិទ្យាសាស្ត្រ / អ៊ិចរ៉េ (X-Ray)",
                                "description": "សេវាថតឆ្លុះកាំរស្មីអ៊ិចវិភាគឆ្អឹង សួត និងសរីរាង្គខាងក្នុង។",
                            },
                            {
                                "title": "សេវាអមវេជ្ជសាស្ត្រ និងជំនួយ: អេកូសាស្ត្រ (Echography)",
                                "description": "សេវាពិនិត្យអេកូពោះ អេកូគភ៌ និងសរីរាង្គផ្សេងៗ។",
                            },
                            {
                                "title": "សេវាអមវេជ្ជសាស្ត្រ និងជំនួយ: ផ្ទះបាយ (Kitchen)",
                                "description": "សេវាផ្គត់ផ្គង់ និងរៀបចំអាហារូបត្ថម្ភសម្រាប់អ្នកជំងឺសម្រាកព្យាបាល។",
                            },
                        ],
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
                "facebook": "https://www.facebook.com/profile.php?id=100068634422929",
                "youtube": "https://www.youtube.com/@3k3n0r",
                "tiktok": "https://www.tiktok.com/@kcnprh",
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


@bp.get("/csrf")
def csrf_token():
    return jsonify({"csrfToken": generate_csrf()})


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
@limiter.limit("10 per minute", methods=["POST"])
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


@bp.get("/visitor-count")
def visitor_count():
    return jsonify({"visitorCount": get_visitor_count()})


@bp.post("/track-visit")
@csrf.exempt
@limiter.limit("60 per minute")
def track_visit():
    count = increment_visitor_count(1)
    return jsonify({"visitorCount": count, "success": True})

