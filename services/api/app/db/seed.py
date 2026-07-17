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
    LinguisticAssetStatus,
    LinguisticLanguage,
    LinguisticRegister,
    LinguisticScript,
    MessageItemSource,
    MessageItemType,
    ModelStatus,
    RiskLevel,
    SemanticConceptType,
    SignStatus,
    UserRoleName,
)
from app.models.linguistics import (
    LinguisticEntry,
    MessageTemplate,
    SemanticConcept,
    SignSemanticMapping,
)
from app.models.message import Message, MessageItem
from app.models.sign import ModelVersion, Sign, SignCategory
from app.models.speech import SpeechVoice
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

CONCEPTS = [
    ("AFFIRMATION_YES", "oui", "yes", SemanticConceptType.AFFIRMATION),
    ("NEGATION_NO", "non", "no", SemanticConceptType.NEGATION),
    ("REQUEST_HELP", "demande d'aide", "request help", SemanticConceptType.ACTION),
    ("OBJECT_WATER", "eau", "water", SemanticConceptType.OBJECT),
    ("PERSON_DOCTOR", "medecin", "doctor", SemanticConceptType.PERSON),
    ("HEALTH_PAIN", "douleur", "pain", SemanticConceptType.HEALTH),
    ("POLITENESS_THANKS", "merci", "thanks", SemanticConceptType.POLITENESS),
    ("ACTION_WANT", "vouloir", "want", SemanticConceptType.ACTION),
    ("QUESTION_WHERE", "ou", "where", SemanticConceptType.QUESTION),
    ("EMERGENCY_ALERT", "urgence", "emergency", SemanticConceptType.EMERGENCY),
]

SIGN_CONCEPTS = {
    "YES": "AFFIRMATION_YES",
    "NO": "NEGATION_NO",
    "HELP": "REQUEST_HELP",
    "WATER": "OBJECT_WATER",
    "DOCTOR": "PERSON_DOCTOR",
    "PAIN": "HEALTH_PAIN",
    "THANKS": "POLITENESS_THANKS",
    "WANT": "ACTION_WANT",
    "WHERE": "QUESTION_WHERE",
    "EMERGENCY": "EMERGENCY_ALERT",
}

LINGUISTIC_ENTRIES = {
    "AFFIRMATION_YES": ("إيه", "iyeh", "oui", "yes"),
    "NEGATION_NO": ("لا", "la", "non", "no"),
    "REQUEST_HELP": ("عاونوني", "awnouni", "aidez-moi", "help me"),
    "OBJECT_WATER": ("الما", "lma", "de l'eau", "water"),
    "PERSON_DOCTOR": ("الطبيب", "tbib", "le medecin", "the doctor"),
    "HEALTH_PAIN": ("الألم", "lalam", "douleur", "pain"),
    "POLITENESS_THANKS": ("شكرا", "shukran", "merci", "thank you"),
    "ACTION_WANT": ("بغيت", "bghit", "je veux", "I want"),
    "QUESTION_WHERE": ("فين", "fin", "ou", "where"),
    "EMERGENCY_ALERT": ("مستعجل", "mestaajel", "urgence", "emergency"),
}

MESSAGE_TEMPLATES = [
    (
        "WANT_OBJECT",
        "Je veux un objet",
        "بغيت حاجة",
        "I want an object",
        "needs",
        RiskLevel.NORMAL,
        {
            "required": ["ACTION_WANT", "OBJECT"],
            "optional": [],
            "darija_arabic": "{action} {object}",
            "darija_latin": "{action_latin} {object_latin}",
            "french": "Je veux {object}.",
            "english": "I want {object}.",
        },
    ),
    (
        "WHERE_PERSON",
        "Ou est la personne",
        "فين كاين الشخص",
        "Where is the person",
        "question",
        RiskLevel.NORMAL,
        {
            "required": ["QUESTION_WHERE", "PERSON"],
            "optional": [],
            "darija_arabic": "{question} كاين {person}",
            "darija_latin": "{question_latin} kayn {person_latin}",
            "french": "Ou est {person} ?",
            "english": "Where is {person}?",
        },
    ),
    (
        "PERSON_WHERE",
        "Personne ou",
        "الشخص فين",
        "Person where",
        "question",
        RiskLevel.NORMAL,
        {
            "required": ["QUESTION_WHERE", "PERSON"],
            "optional": [],
            "darija_arabic": "{person} {question}",
            "darija_latin": "{person_latin} {question_latin}",
            "french": "{person}, ou ?",
            "english": "{person}, where?",
        },
    ),
    (
        "REQUEST_HELP",
        "Demander de l'aide",
        "طلب المساعدة",
        "Request help",
        "needs",
        RiskLevel.SENSITIVE,
        {
            "required": ["REQUEST_HELP"],
            "optional": [],
            "darija_arabic": "{request}",
            "darija_latin": "{request_latin}",
            "french": "Aidez-moi.",
            "english": "Help me.",
        },
    ),
    (
        "HEALTH_TERM",
        "Terme de sante",
        "كلمة صحية",
        "Health term",
        "health",
        RiskLevel.MEDICAL,
        {
            "required": ["HEALTH"],
            "optional": [],
            "darija_arabic": "{health}",
            "darija_latin": "{health_latin}",
            "french": "{health}.",
            "english": "{health}.",
        },
    ),
    (
        "EMERGENCY_ALERT",
        "Urgence",
        "حالة مستعجلة",
        "Emergency",
        "emergency",
        RiskLevel.EMERGENCY,
        {
            "required": ["EMERGENCY_ALERT"],
            "optional": [],
            "darija_arabic": "{emergency}",
            "darija_latin": "{emergency_latin}",
            "french": "Urgence.",
            "english": "Emergency.",
        },
    ),
]

SPEECH_VOICES = [
    (
        "darija-default",
        "local-darija",
        "opensign-tone-ary-ma-1",
        "Voix synthétique expérimentale en Darija",
        "ary-MA",
        "ary-MA",
        "opensign-tone-v1",
        {"license": "Apache-2.0 project code; no external weights bundled"},
        True,
    ),
    (
        "arabic-fallback",
        "local-arabic-fallback",
        "opensign-tone-ar-1",
        "Voix arabe de secours",
        "ar",
        "ar",
        "opensign-tone-v1",
        {"license": "Apache-2.0 project code; not a native Darija voice"},
        False,
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

        for (
            voice_id,
            provider,
            voice_code,
            display_name,
            language,
            locale,
            model_version,
            license_info,
            is_default,
        ) in SPEECH_VOICES:
            voice = db.get(SpeechVoice, voice_id)
            if voice is None:
                db.add(
                    SpeechVoice(
                        id=voice_id,
                        provider=provider,
                        voice_code=voice_code,
                        display_name=display_name,
                        language=language,
                        locale=locale,
                        model_version=model_version,
                        license_info=license_info,
                        is_active=True,
                        is_default=is_default,
                        is_experimental=True,
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
        concept_by_code: dict[str, SemanticConcept] = {}
        for code, name_fr, name_en, concept_type in CONCEPTS:
            concept = db.scalar(select(SemanticConcept).where(SemanticConcept.code == code))
            if concept is None:
                concept = SemanticConcept(
                    code=code,
                    name_fr=name_fr,
                    name_en=name_en,
                    description=(
                        "Donnee linguistique de demonstration; validation communautaire requise."
                    ),
                    concept_type=concept_type,
                    is_active=True,
                )
                db.add(concept)
                db.flush()
            concept_by_code[code] = concept

        for sign_code, concept_code in SIGN_CONCEPTS.items():
            sign = signs_by_code.get(sign_code)
            concept = concept_by_code.get(concept_code)
            if sign and concept:
                existing = db.scalar(
                    select(SignSemanticMapping).where(
                        SignSemanticMapping.sign_id == sign.id,
                        SignSemanticMapping.semantic_concept_id == concept.id,
                    )
                )
                if existing is None:
                    db.add(
                        SignSemanticMapping(
                            sign_id=sign.id,
                            semantic_concept_id=concept.id,
                            priority=10,
                            context="demo-primary",
                            is_default=True,
                        )
                    )

        for concept_code, (darija_ar, darija_latin, french, english) in LINGUISTIC_ENTRIES.items():
            concept = concept_by_code[concept_code]
            entries = [
                (LinguisticLanguage.DARIJA, LinguisticScript.ARABIC, darija_ar, "default"),
                (LinguisticLanguage.DARIJA, LinguisticScript.LATIN, darija_latin, "default"),
                (
                    LinguisticLanguage.DARIJA,
                    LinguisticScript.LATIN_ARABIZI,
                    darija_latin.replace("a", "a").replace("awnouni", "3awnouni"),
                    "arabizi",
                ),
                (LinguisticLanguage.FRENCH, LinguisticScript.LATIN, french, "default"),
                (LinguisticLanguage.ENGLISH, LinguisticScript.LATIN, english, "default"),
            ]
            for language, script, value, variant in entries:
                existing_entry = db.scalar(
                    select(LinguisticEntry).where(
                        LinguisticEntry.semantic_concept_id == concept.id,
                        LinguisticEntry.language == language,
                        LinguisticEntry.script == script,
                        LinguisticEntry.variant == variant,
                    )
                )
                if existing_entry is None:
                    db.add(
                        LinguisticEntry(
                            semantic_concept_id=concept.id,
                            language=language,
                            script=script,
                            value=value,
                            variant=variant,
                            register=LinguisticRegister.NEUTRAL,
                            is_default=True,
                            is_active=True,
                        )
                    )

        for (
            code,
            name_fr,
            name_ar,
            name_en,
            template_category,
            risk,
            structure,
        ) in MESSAGE_TEMPLATES:
            if not db.scalar(select(MessageTemplate).where(MessageTemplate.code == code)):
                db.add(
                    MessageTemplate(
                        code=code,
                        name_fr=name_fr,
                        name_ar=name_ar,
                        name_en=name_en,
                        category=template_category,
                        template_structure=structure,
                        risk_level=risk,
                        status=LinguisticAssetStatus.ACTIVE,
                        version="demo-1.0.0",
                        is_active=True,
                    )
                )

        for sign in signs_by_code.values():
            existing_campaign_sign = db.scalar(
                select(CampaignSign).where(
                    CampaignSign.campaign_id == campaign.id,
                    CampaignSign.sign_id == sign.id,
                )
            )
            if existing_campaign_sign is None:
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
        if admin:
            demo_message = db.scalar(select(Message).where(Message.title == "Demo - besoin d'eau"))
            if demo_message is None:
                demo_message = Message(
                    user_id=admin.id,
                    title="Demo - besoin d'eau",
                    raw_semantic_sequence=["ACTION_WANT", "OBJECT_WATER"],
                    generated_darija_arabic="بغيت الما",
                    generated_darija_latin="bghit lma",
                    generated_french="Je veux de l'eau.",
                    generated_english="I want water.",
                    final_darija_arabic="بغيت الما",
                    final_darija_latin="bghit lma",
                    final_french="Je veux de l'eau.",
                    final_english="I want water.",
                    generation_metadata={"demo": True, "template": "WANT_OBJECT"},
                    is_favorite=True,
                )
                db.add(demo_message)
                db.flush()
                for position, concept_code in enumerate(["ACTION_WANT", "OBJECT_WATER"], start=1):
                    sign_code = "WANT" if concept_code == "ACTION_WANT" else "WATER"
                    db.add(
                        MessageItem(
                            message_id=demo_message.id,
                            position=position,
                            item_type=MessageItemType.CONFIRMED_SIGN,
                            sign_id=signs_by_code[sign_code].id,
                            semantic_concept_id=concept_by_code[concept_code].id,
                            source=MessageItemSource.TEMPLATE,
                            display_label=concept_by_code[concept_code].name_fr,
                            metadata_json={"demo": True},
                        )
                    )
        db.commit()


if __name__ == "__main__":
    seed()
