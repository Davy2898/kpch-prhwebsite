from datetime import datetime
from typing import Optional
from . import db


class Admin(db.Model):
    __tablename__ = "tbladmin"
    __table_args__ = {"schema": "newsportal"}

    id = db.Column("id", db.BigInteger, primary_key=True)
    AdminUserName = db.Column("adminusername", db.String(255), index=True, unique=True)
    AdminPassword = db.Column("adminpassword", db.String(255))
    AdminEmailId = db.Column("adminemailid", db.String(255))
    userType = db.Column("usertype", db.BigInteger)  # 1=admin,0=subadmin per sample
    CreationDate = db.Column("creationdate", db.DateTime(timezone=True), default=datetime.utcnow)
    UpdationDate = db.Column("updationdate", db.DateTime(timezone=True), onupdate=datetime.utcnow)

    posts = db.relationship("Post", back_populates="author", primaryjoin="Admin.AdminUserName==Post.postedBy")


class Category(db.Model):
    __tablename__ = "tblcategory"
    __table_args__ = {"schema": "newsportal"}

    id = db.Column("id", db.BigInteger, primary_key=True)
    CategoryName = db.Column("categoryname", db.String(200))
    Description = db.Column("description", db.Text)
    PostingDate = db.Column("postingdate", db.DateTime(timezone=True), default=datetime.utcnow)
    UpdationDate = db.Column("updationdate", db.DateTime(timezone=True), onupdate=datetime.utcnow)
    Is_Active = db.Column("is_active", db.BigInteger)

    subcategories = db.relationship("SubCategory", back_populates="category", cascade="all,delete")
    posts = db.relationship("Post", back_populates="category")


class SubCategory(db.Model):
    __tablename__ = "tblsubcategory"
    __table_args__ = {"schema": "newsportal"}

    SubCategoryId = db.Column("subcategoryid", db.BigInteger, primary_key=True)
    CategoryId = db.Column("categoryid", db.BigInteger, db.ForeignKey("newsportal.tblcategory.id"))
    Subcategory = db.Column("subcategory", db.String(255))
    SubCatDescription = db.Column("subcatdescription", db.Text)
    PostingDate = db.Column("postingdate", db.DateTime(timezone=True), default=datetime.utcnow)
    UpdationDate = db.Column("updationdate", db.DateTime(timezone=True), onupdate=datetime.utcnow)
    Is_Active = db.Column("is_active", db.BigInteger)

    category = db.relationship("Category", back_populates="subcategories")
    posts = db.relationship("Post", back_populates="subcategory")


class Post(db.Model):
    __tablename__ = "tblposts"
    __table_args__ = {"schema": "newsportal"}

    id = db.Column("id", db.BigInteger, primary_key=True)
    PostTitle = db.Column("posttitle", db.Text)
    CategoryId = db.Column("categoryid", db.BigInteger, db.ForeignKey("newsportal.tblcategory.id"), index=True)
    SubCategoryId = db.Column("subcategoryid", db.BigInteger, db.ForeignKey("newsportal.tblsubcategory.subcategoryid"), index=True)
    PostDetails = db.Column("postdetails", db.Text)
    PostingDate = db.Column("postingdate", db.DateTime(timezone=True), default=datetime.utcnow)
    UpdationDate = db.Column("updationdate", db.DateTime(timezone=True), onupdate=datetime.utcnow)
    Is_Active = db.Column("is_active", db.BigInteger)
    PostUrl = db.Column("posturl", db.Text)
    PostImage = db.Column("postimage", db.String(255))
    viewCounter = db.Column("viewcounter", db.BigInteger)
    postedBy = db.Column("postedby", db.String(255), db.ForeignKey("newsportal.tbladmin.adminusername"))
    lastUpdatedBy = db.Column("lastupdatedby", db.String(255))

    category = db.relationship("Category", back_populates="posts")
    subcategory = db.relationship("SubCategory", back_populates="posts")
    author = db.relationship("Admin", back_populates="posts", primaryjoin="Admin.AdminUserName==Post.postedBy")
    comments = db.relationship("Comment", back_populates="post", cascade="all,delete-orphan")


class Comment(db.Model):
    __tablename__ = "tblcomments"
    __table_args__ = {"schema": "newsportal"}

    id = db.Column("id", db.BigInteger, primary_key=True)
    postId = db.Column("postid", db.BigInteger, db.ForeignKey("newsportal.tblposts.id"), index=True)
    name = db.Column("name", db.String(120))
    email = db.Column("email", db.String(150))
    comment = db.Column("comment", db.Text)
    postingDate = db.Column("postingdate", db.DateTime(timezone=True), default=datetime.utcnow)
    status = db.Column("status", db.BigInteger)  # 1=approved,0=pending

    post = db.relationship("Post", back_populates="comments")


class Page(db.Model):
    __tablename__ = "tblpages"
    __table_args__ = {"schema": "newsportal"}

    id = db.Column("id", db.BigInteger, primary_key=True)
    PageName = db.Column("pagename", db.String(200))
    PageTitle = db.Column("pagetitle", db.Text)
    Description = db.Column("description", db.Text)
    PostingDate = db.Column("postingdate", db.DateTime(timezone=True), default=datetime.utcnow)
    UpdationDate = db.Column("updationdate", db.DateTime(timezone=True), onupdate=datetime.utcnow)


class User(db.Model):
    __tablename__ = "tblusers"
    __table_args__ = {"schema": "newsportal"}

    userId = db.Column("userid", db.BigInteger, primary_key=True)
    fullName = db.Column("fullname", db.String(255))
    emailId = db.Column("emailid", db.String(255))
    conatctNo = db.Column("conatctno", db.BigInteger)
    address = db.Column("address", db.Text)
    regDate = db.Column("regdate", db.BigInteger)  # Kept as-is to reflect source schema
    isActive = db.Column("isactive", db.BigInteger)


class SiteSetting(db.Model):
    __tablename__ = "tblsitesettings"
    __table_args__ = {"schema": "newsportal"}

    id = db.Column("id", db.Integer, primary_key=True, autoincrement=True)
    settingKey = db.Column("setting_key", db.String(100), unique=True, index=True)
    settingValue = db.Column("setting_value", db.Text)
    updatedAt = db.Column("updated_at", db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


def get_visitor_count() -> int:
    try:
        setting = SiteSetting.query.filter_by(settingKey="visitor_count").first()
        if not setting:
            setting = SiteSetting(settingKey="visitor_count", settingValue="4022694")
            db.session.add(setting)
            db.session.commit()
            return 4022694
        return int(setting.settingValue)
    except Exception:
        db.session.rollback()
        return 4022694


def increment_visitor_count(step: int = 1) -> int:
    try:
        setting = SiteSetting.query.filter_by(settingKey="visitor_count").first()
        if not setting:
            current = 4022694 + step
            setting = SiteSetting(settingKey="visitor_count", settingValue=str(current))
            db.session.add(setting)
        else:
            try:
                current = int(setting.settingValue) + step
            except (ValueError, TypeError):
                current = 4022694 + step
            setting.settingValue = str(current)
            setting.updatedAt = datetime.utcnow()
        db.session.commit()
        return current
    except Exception:
        db.session.rollback()
        return get_visitor_count()


def set_visitor_count(new_count: int) -> int:
    try:
        setting = SiteSetting.query.filter_by(settingKey="visitor_count").first()
        if not setting:
            setting = SiteSetting(settingKey="visitor_count", settingValue=str(new_count))
            db.session.add(setting)
        else:
            setting.settingValue = str(new_count)
            setting.updatedAt = datetime.utcnow()
        db.session.commit()
        return new_count
    except Exception:
        db.session.rollback()
        return get_visitor_count()


