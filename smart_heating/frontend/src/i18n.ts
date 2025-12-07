import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import translationEN from './locales/en/translation.json'
import translationNL from './locales/nl/translation.json'

const resources = {
  en: {
    translation: translationEN
  },
  nl: {
    translation: translationNL
  }
}

// Custom language detector that checks Home Assistant language first
const haLanguageDetector = {
  name: 'haLanguageDetector',
  lookup(): string | undefined {
    // Try to get language from Home Assistant
    // HA stores language in localStorage or we can detect from browser
    const haLang = localStorage.getItem('selectedLanguage')
    if (haLang) {
      // Map HA language codes to our supported languages
      if (haLang.startsWith('nl')) return 'nl'
      if (haLang.startsWith('en')) return 'en'
    }
    return undefined
  },
  cacheUserLanguage(lng: string) {
    localStorage.setItem('selectedLanguage', lng)
  }
}

const languageDetector = new LanguageDetector()
languageDetector.addDetector(haLanguageDetector)

i18n
  .use(languageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    supportedLngs: ['en', 'nl'],
    detection: {
      order: ['haLanguageDetector', 'navigator', 'htmlTag'],
      caches: ['localStorage']
    },
    interpolation: {
      escapeValue: false // React already escapes
    }
  })

export default i18n
