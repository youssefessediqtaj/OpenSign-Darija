from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.dataset import (
    CampaignSign,
    CollectionCampaign,
    ConsentTemplate,
    ContributorProfile,
    DatasetVersion,
)
from app.models.enums import (
    CampaignStatus,
    DatasetVersionStatus,
    ModelStatus,
    RiskLevel,
    SignStatus,
    UserRoleName,
)
from app.models.sign import ModelVersion, Sign, SignCategory
from app.models.user import Role, User, UserRole
from app.security.passwords import hash_password

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

DEV_USERS: list[tuple[str, str, str]] = [
    ("contributor@example.test", "Contributor Demo", "CONTRIBUTOR"),
    ("linguist@example.test", "Linguist Reviewer Demo", "LINGUIST_REVIEWER"),
    ("ml-reviewer@example.test", "ML Reviewer Demo", "ML_REVIEWER"),
    ("admin@example.test", "Admin Demo", "ADMIN"),
]

CONSENT_TEMPLATES = [
    (
        "dataset-collection",
        "1.0.0",
        "Consentement pour contribuer au dataset OpenSign Darija",
        (
            "Choisissez separement les traitements de landmarks, la conservation, "
            "la video et les usages futurs."
        ),
        (
            "OpenSign Darija collecte des points de mouvement et, seulement si vous l'autorisez, "
            "des videos privees pour constituer un dataset de Langue des Signes Marocaine. "
            "Les landmarks decrivent des mouvements corporels et peuvent rester sensibles. "
            "Vous pouvez refuser la video et retirer vos consentements pour les futures versions."
        ),
        "fr",
    ),
    (
        "dataset-collection",
        "1.0.0",
        "Consent for OpenSign Darija dataset contribution",
        "Choose landmark, storage, video, and future-use consent separately.",
        (
            "OpenSign Darija stores movement landmarks and, only with explicit "
            "permission, private videos. "
            "Landmarks are motion data and are not fully anonymous."
        ),
        "en",
    ),
    (
        "dataset-collection",
        "1.0.0",
        "الموافقة على المساهمة في بيانات OpenSign Darija",
        "اختار الموافقات ديال النقاط، التخزين، الفيديو، والاستعمالات القادمة بشكل منفصل.",
        "OpenSign Darija كيخزن نقاط الحركة وفيديو خاص غير إلا وافقتي صراحة.",
        "ar",
    ),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for role_enum, description in ROLE_DESCRIPTIONS.items():
            if not db.scalar(select(Role).where(Role.name == role_enum.value)):
                db.add(Role(name=role_enum.value, description=description))
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
        role_by_name = {role.name: role for role in db.scalars(select(Role)).all()}
        for email, display_name, role_name in DEV_USERS:
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    display_name=display_name,
                    password_hash=hash_password("OpenSignDemo123!"),
                    is_verified=True,
                )
                db.add(user)
                db.flush()
            role = role_by_name[role_name]
            if not any(user_role.role_id == role.id for user_role in user.roles):
                user.roles.append(UserRole(role=role))
            if role_name == "CONTRIBUTOR":
                profile = db.scalar(
                    select(ContributorProfile).where(ContributorProfile.user_id == user.id)
                )
                if profile is None:
                    db.add(
                        ContributorProfile(
                            user_id=user.id,
                            public_id="signer_000001",
                            preferred_interface_language="fr",
                            region="UNCONFIRMED",
                        )
                    )

        for code, version, title, summary, full_text, language in CONSENT_TEMPLATES:
            if not db.scalar(
                select(ConsentTemplate).where(
                    ConsentTemplate.code == code,
                    ConsentTemplate.version == version,
                    ConsentTemplate.language == language,
                )
            ):
                db.add(
                    ConsentTemplate(
                        code=code,
                        version=version,
                        title=title,
                        summary=summary,
                        full_text=full_text,
                        language=language,
                        is_active=True,
                    )
                )

        campaign = db.scalar(
            select(CollectionCampaign).where(CollectionCampaign.slug == "pilot-lsm-maroc-10")
        )
        if campaign is None:
            campaign = CollectionCampaign(
                name="Pilote Langue des Signes Marocaine - 10 signes",
                slug="pilot-lsm-maroc-10",
                description=(
                    "Campagne de demonstration pour collecter plusieurs repetitions consenties "
                    "des dix signes initiaux. Les videos restent privees et optionnelles."
                ),
                status=CampaignStatus.ACTIVE,
                target_sign_count=10,
                target_repetitions_per_sign=5,
                minimum_repetitions_per_submission=3,
                maximum_repetitions_per_submission=8,
            )
            db.add(campaign)
            db.flush()
        signs_by_code = {sign.code: sign for sign in db.scalars(select(Sign)).all()}
        for sign in signs_by_code.values():
            existing = db.scalar(
                select(CampaignSign).where(
                    CampaignSign.campaign_id == campaign.id,
                    CampaignSign.sign_id == sign.id,
                )
            )
            if existing is None:
                db.add(
                    CampaignSign(
                        campaign_id=campaign.id,
                        sign_id=sign.id,
                        target_repetitions=5,
                        instruction_text=(
                            f"Enregistrez le signe {sign.french_translation}. "
                            "Utilisez uniquement une demonstration validee par votre communaute; "
                            "ne copiez pas un signe ASL."
                        ),
                        requires_face=True,
                        requires_pose=True,
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
        admin = db.scalar(select(User).where(User.email == "admin@example.test"))
        existing_dataset = db.scalar(
            select(DatasetVersion).where(DatasetVersion.name == "opensign-darija-pilot")
        )
        if admin and not existing_dataset:
            db.add(
                DatasetVersion(
                    name="opensign-darija-pilot",
                    semantic_version="0.1.0",
                    status=DatasetVersionStatus.DRAFT,
                    description="Version brouillon de demonstration; ne pas publier.",
                    feature_schema_version="1.0.0",
                    created_by=admin.id,
                )
            )
        db.commit()


if __name__ == "__main__":
    seed()
