from datetime import UTC, datetime

from sqlalchemy import func

from app import db
from app.models import Category, SubCategory
from run_local import app


CATEGORIES = {
    "Hospital News": ["Announcements", "Events", "Meetings", "Official Visits"],
    "Health Education": [
        "Disease Prevention",
        "Mother & Child Health",
        "Nutrition",
        "Mental Health",
        "Eye Care",
    ],
    "Hospital Services": [
        "Emergency",
        "OPD",
        "Surgery",
        "Maternity",
        "Eye Department",
        "Laboratory",
        "X-Ray",
    ],
    "Public Notices": ["Opening Hours", "Holiday Notice", "Service Changes", "Patient Guidelines"],
    "Community Activities": [
        "Outreach Program",
        "Vaccination Campaign",
        "Blood Donation",
        "Health Screening",
    ],
    "Training & Workshop": [
        "Staff Training",
        "Medical Workshop",
        "Quality Improvement",
        "Safety Training",
    ],
    "Leadership & Administration": [
        "Director Updates",
        "Staff Meeting",
        "Partner Visit",
        "Provincial Health Department",
    ],
    "Donations & Partnerships": [
        "Equipment Donation",
        "NGO Partner",
        "Government Support",
        "Community Support",
    ],
}


def next_category_id() -> int:
    return (db.session.query(func.max(Category.id)).scalar() or 0) + 1


def next_subcategory_id() -> int:
    return (db.session.query(func.max(SubCategory.SubCategoryId)).scalar() or 0) + 1


with app.app_context():
    now = datetime.now(UTC)
    created_categories = 0
    created_subcategories = 0

    for category_name, subcategory_names in CATEGORIES.items():
        category = Category.query.filter_by(CategoryName=category_name).first()
        if category is None:
            category = Category(
                id=next_category_id(),
                CategoryName=category_name,
                Description=f"{category_name} posts",
                PostingDate=now,
                Is_Active=1,
            )
            db.session.add(category)
            db.session.flush()
            created_categories += 1
        else:
            category.Is_Active = 1

        for subcategory_name in subcategory_names:
            subcategory = SubCategory.query.filter_by(
                CategoryId=category.id,
                Subcategory=subcategory_name,
            ).first()
            if subcategory is None:
                db.session.add(
                    SubCategory(
                        SubCategoryId=next_subcategory_id(),
                        CategoryId=category.id,
                        Subcategory=subcategory_name,
                        SubCatDescription=f"{subcategory_name} posts",
                        PostingDate=now,
                        Is_Active=1,
                    )
                )
                db.session.flush()
                created_subcategories += 1
            else:
                subcategory.Is_Active = 1

    db.session.commit()

    print(f"created_categories={created_categories}")
    print(f"created_subcategories={created_subcategories}")
    print("recommended_category=Hospital News")
    print("recommended_subcategory=Meetings")
