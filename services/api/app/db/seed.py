from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.enums import ModelStatus, RiskLevel, SignStatus, UserRoleName
from app.models.sign import ModelVersion, Sign, SignCategory
from app.models.user import Role

ROLE_DESCRIPTIONS = {
    UserRoleName.USER: "Compte utilisateur standard",
    UserRoleName.CONTRIBUTOR: "Contribution aux donnees et corrections",
    UserRoleName.LINGUIST_REVIEWER: "Relecture linguistique",
    UserRoleName.ML_REVIEWER: "Relecture machine learning",
    UserRoleName.ADMIN: "Administration de la plateforme",
}

CATEGORIES = [
    ("besoins-essentiels", "Besoins essentiels", "احتياجات أساسية", "Essential needs"),
    ("sante", "Sante", "الصحة", "Health"),
    ("quotidien", "Quotidien", "اليومي", "Daily life"),
    ("personnes", "Personnes", "الناس", "People"),
    ("questions", "Questions", "أسئلة", "Questions"),
    ("actions", "Actions", "أفعال", "Actions"),
]

SIGNS = [
    (
        "YES",
        "oui",
        "oui",
        "إيه",
        "iyeh",
        "oui",
        "yes",
        "questions",
        SignStatus.ACTIVE,
        RiskLevel.NORMAL,
    ),
    ("NO", "non", "non", "لا", "la", "non", "no", "questions", SignStatus.ACTIVE, RiskLevel.NORMAL),
    (
        "HELP",
        "aide",
        "aide",
        "عاونّي",
        "aweni",
        "aide",
        "help",
        "besoins-essentiels",
        SignStatus.ACTIVE,
        RiskLevel.SENSITIVE,
    ),
    (
        "WATER",
        "eau",
        "eau",
        "ما",
        "ma",
        "eau",
        "water",
        "besoins-essentiels",
        SignStatus.ACTIVE,
        RiskLevel.NORMAL,
    ),
    (
        "DOCTOR",
        "medecin",
        "medecin",
        "طبيب",
        "tbib",
        "medecin",
        "doctor",
        "sante",
        SignStatus.EXPERIMENTAL,
        RiskLevel.MEDICAL,
    ),
    (
        "PAIN",
        "douleur",
        "douleur",
        "وجع",
        "wjae",
        "douleur",
        "pain",
        "sante",
        SignStatus.EXPERIMENTAL,
        RiskLevel.MEDICAL,
    ),
    (
        "THANKS",
        "merci",
        "merci",
        "شكرا",
        "shukran",
        "merci",
        "thanks",
        "quotidien",
        SignStatus.ACTIVE,
        RiskLevel.NORMAL,
    ),
    (
        "WANT",
        "vouloir",
        "vouloir",
        "بغيت",
        "bghit",
        "vouloir",
        "want",
        "actions",
        SignStatus.ACTIVE,
        RiskLevel.NORMAL,
    ),
    (
        "WHERE",
        "ou",
        "ou",
        "فين",
        "fin",
        "ou",
        "where",
        "questions",
        SignStatus.ACTIVE,
        RiskLevel.NORMAL,
    ),
    (
        "EMERGENCY",
        "urgence",
        "urgence",
        "مستعجل",
        "mestaajel",
        "urgence",
        "emergency",
        "sante",
        SignStatus.EXPERIMENTAL,
        RiskLevel.EMERGENCY,
    ),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for role_name, description in ROLE_DESCRIPTIONS.items():
            if not db.scalar(select(Role).where(Role.name == role_name.value)):
                db.add(Role(name=role_name.value, description=description))
        db.flush()

        category_by_slug: dict[str, SignCategory] = {}
        for slug, name_fr, name_ar, name_en in CATEGORIES:
            category = db.scalar(select(SignCategory).where(SignCategory.slug == slug))
            if category is None:
                category = SignCategory(
                    slug=slug, name_fr=name_fr, name_ar=name_ar, name_en=name_en, description=""
                )
                db.add(category)
                db.flush()
            category_by_slug[slug] = category

        for code, slug, meaning, ar, latin, fr, en, category_slug, status, risk in SIGNS:
            if not db.scalar(select(Sign).where(Sign.code == code)):
                db.add(
                    Sign(
                        code=code,
                        slug=slug,
                        canonical_meaning=meaning,
                        darija_arabic=ar,
                        darija_latin=latin,
                        french_translation=fr,
                        english_translation=en,
                        category_id=category_by_slug[category_slug].id,
                        status=status,
                        risk_level=risk,
                        is_active=True,
                    )
                )
        if not db.scalar(select(ModelVersion).where(ModelVersion.name == "opensign-darija-mock")):
            db.add(
                ModelVersion(
                    name="opensign-darija-mock",
                    semantic_version="0.1.0",
                    status=ModelStatus.ACTIVE,
                    vocabulary_size=10,
                    description="Modele simule pour tester le flux de reconnaissance.",
                    metrics_json={"mock": True},
                    artifact_path="mock://opensign-darija",
                    is_active=True,
                )
            )
        db.commit()


if __name__ == "__main__":
    seed()
