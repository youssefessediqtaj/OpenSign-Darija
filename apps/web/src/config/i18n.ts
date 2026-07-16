import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';

void i18next.use(initReactI18next).init({
  lng: 'fr',
  fallbackLng: 'fr',
  interpolation: { escapeValue: false },
  resources: {
    fr: {
      translation: {
        project: 'OpenSign Darija',
        cameraPermission: 'Autorisation camera',
        cameraDenied: "L'acces a la camera a ete refuse.",
        noCamera: "Aucune camera compatible n'a ete detectee.",
        framing: 'Cadrage',
        lighting: 'Luminosite',
        stability: 'Stabilite',
        countdown: 'Compte a rebours',
        capture: 'Capture',
        processing: 'Traitement',
        result: 'Resultat',
        privacyCamera:
          'La video est analysee sur votre appareil. Seuls les points de mouvement sont envoyes.',
      },
    },
    ar: {
      translation: {
        project: 'OpenSign Darija',
        cameraPermission: 'إذن الكاميرا',
        cameraDenied: 'تم رفض الوصول إلى الكاميرا.',
        noCamera: 'لم يتم العثور على كاميرا متوافقة.',
        framing: 'التأطير',
        lighting: 'الإضاءة',
        stability: 'الثبات',
        countdown: 'العد التنازلي',
        capture: 'التقاط',
        processing: 'معالجة',
        result: 'النتيجة',
        privacyCamera: 'تتم معالجة الفيديو على جهازك. يتم إرسال نقاط الحركة فقط.',
      },
    },
    en: {
      translation: {
        project: 'OpenSign Darija',
        cameraPermission: 'Camera permission',
        cameraDenied: 'Camera access was denied.',
        noCamera: 'No compatible camera was detected.',
        framing: 'Framing',
        lighting: 'Lighting',
        stability: 'Stability',
        countdown: 'Countdown',
        capture: 'Capture',
        processing: 'Processing',
        result: 'Result',
        privacyCamera:
          'Video is processed on your device. Only motion landmarks are sent.',
      },
    },
  },
});
