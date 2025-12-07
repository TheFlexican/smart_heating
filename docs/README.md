# Documentation Structure

This directory contains language-specific documentation for the Smart Heating integration.

## Languages

- **English** (`en/`) - Default language
- **Dutch** (`nl/`) - Nederlandse documentatie

## Structure

```
docs/
├── README.md (this file)
├── en/                       # English documentation
│   ├── ARCHITECTURE.md       # Technical architecture overview
│   └── DEVELOPER.md          # Developer quick reference
└── nl/                       # Dutch documentation
    ├── ARCHITECTURE.md       # Technische architectuur overzicht
    └── DEVELOPER.md          # Ontwikkelaar snelle referentie
```

## Root-Level Documentation

For quick access, the following files remain at the repository root:

- **English:**
  - `README.md` - User documentation
  - `CHANGELOG.md` - Version history
  - `ARCHITECTURE.md` - Technical architecture (symlinked/copy of `docs/en/ARCHITECTURE.md`)
  - `DEVELOPER.md` - Developer guide (symlinked/copy of `docs/en/DEVELOPER.md`)

- **Dutch:**
  - `README.nl.md` - Gebruikers documentatie
  - `CHANGELOG.nl.md` - Versie geschiedenis

## Documentation Maintenance

**IMPORTANT:** When updating technical documentation, **ALWAYS update BOTH language versions:**

### Architecture Changes
- ✅ Update `docs/en/ARCHITECTURE.md`
- ✅ Update `docs/nl/ARCHITECTURE.md`
- ✅ Update root `ARCHITECTURE.md` (optional, for quick access)

### Developer Workflow Changes
- ✅ Update `docs/en/DEVELOPER.md`
- ✅ Update `docs/nl/DEVELOPER.md`
- ✅ Update root `DEVELOPER.md` (optional, for quick access)

### User-Facing Feature Changes
- ✅ Update `README.md`
- ✅ Update `README.nl.md`
- ✅ Update `CHANGELOG.md`
- ✅ Update `CHANGELOG.nl.md`

### Frontend Text Changes
- ✅ Update `smart_heating/frontend/src/locales/en/translation.json`
- ✅ Update `smart_heating/frontend/src/locales/nl/translation.json`

## Adding New Languages

To add a new language:

1. **Create directory structure:**
   ```bash
   mkdir -p docs/{lang}
   ```

2. **Copy and translate documentation:**
   ```bash
   cp docs/en/ARCHITECTURE.md docs/{lang}/ARCHITECTURE.md
   cp docs/en/DEVELOPER.md docs/{lang}/DEVELOPER.md
   # Translate the content
   ```

3. **Create root-level README and CHANGELOG:**
   ```bash
   cp README.md README.{lang}.md
   cp CHANGELOG.md CHANGELOG.{lang}.md
   # Translate the content
   ```

4. **Update frontend translations:**
   ```bash
   mkdir -p smart_heating/frontend/src/locales/{lang}
   cp smart_heating/frontend/src/locales/en/translation.json \
      smart_heating/frontend/src/locales/{lang}/translation.json
   # Translate all keys
   ```

5. **Update i18n configuration** (`smart_heating/frontend/src/i18n.ts`):
   ```typescript
   import translation{Lang} from './locales/{lang}/translation.json'
   
   const resources = {
     en: { translation: translationEN },
     nl: { translation: translationNL },
     {lang}: { translation: translation{Lang} }
   }
   ```

6. **Add language to supported list:**
   ```typescript
   supportedLngs: ['en', 'nl', '{lang}']
   ```

7. **Update Header language switcher** (`components/Header.tsx`)

8. **Update this README** with the new language

## Available Documentation

### Technical Documentation
- **ARCHITECTURE.md** - System architecture, components, data flow
- **DEVELOPER.md** - Quick reference for developers, common tasks

### User Documentation
- **README.md** - Installation, configuration, usage guide
- **CHANGELOG.md** - Version history and release notes

### Developer Resources
- **V0.6.0_ARCHITECTURE.md** (root) - v0.6.0 feature architecture
- **V0.6.0_ROADMAP.md** (root) - v0.6.0 implementation plan
- **I18N_IMPLEMENTATION.md** (root) - i18n implementation guide

## Language Coverage

| Document | English | Dutch | Other |
|----------|---------|-------|-------|
| README | ✅ | ✅ | - |
| CHANGELOG | ✅ | ✅ | - |
| ARCHITECTURE | ✅ | ✅ | - |
| DEVELOPER | ✅ | ✅ | - |
| Frontend UI | ✅ | ✅ | - |
| V0.6.0 Specs | ✅ | ❌ | - |

## Translation Status

- ✅ **Complete** - All documentation and UI translated
- 🟡 **Partial** - Some documentation translated
- ❌ **Missing** - No translation available

Current status: **Complete** for English and Dutch
