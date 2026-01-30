import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import en from './en.json'
import zh from './zh.json'

export type Language = 'en' | 'zh'

type TranslationValue = string | string[] | Record<string, unknown>
type Translations = typeof en

const translations: Record<Language, Translations> = { en, zh }

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string, params?: Record<string, string>) => string
  tArray: (key: string) => string[]
}

const STORAGE_KEY = 'app-language'

const LanguageContext = createContext<LanguageContextType | null>(null)

function getNestedValue(obj: Translations, path: string): TranslationValue | undefined {
  const keys = path.split('.')
  let current: unknown = obj
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = (current as Record<string, unknown>)[key]
    } else {
      return undefined
    }
  }
  return current as TranslationValue | undefined
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'en' || stored === 'zh') {
      return stored
    }
    return 'en'
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, language)
  }, [language])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
  }

  const t = (key: string, params?: Record<string, string>): string => {
    const value = getNestedValue(translations[language], key)
    if (typeof value !== 'string') {
      // Fallback to English
      const fallback = getNestedValue(translations.en, key)
      if (typeof fallback !== 'string') {
        return key
      }
      return applyParams(fallback, params)
    }
    return applyParams(value, params)
  }

  const tArray = (key: string): string[] => {
    const value = getNestedValue(translations[language], key)
    if (Array.isArray(value)) {
      return value as string[]
    }
    // Fallback to English
    const fallback = getNestedValue(translations.en, key)
    if (Array.isArray(fallback)) {
      return fallback as string[]
    }
    return []
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, tArray }}>
      {children}
    </LanguageContext.Provider>
  )
}

function applyParams(str: string, params?: Record<string, string>): string {
  if (!params) return str
  return str.replace(/\{(\w+)\}/g, (_, key) => params[key] ?? `{${key}}`)
}

export function useLanguage(): LanguageContextType {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
