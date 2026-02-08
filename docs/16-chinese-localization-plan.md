# Chinese Localization Plan

**Overall Progress:** `100%`

## TLDR
Add full Chinese language support with an explicit language toggle in Settings. Voice commands work bilingually (both EN/CN always recognized). TTS and Q&A responses follow the selected UI language.

## Critical Decisions

- **i18n approach**: Simple key-value JSON locale files (`en.json`, `zh.json`) with a React context provider - no heavy i18n library needed for this scope
- **Voice commands**: Bilingual - both English and Chinese commands are always recognized regardless of UI language
- **TTS voice**: `cmn-CN-Chirp3-HD-Aoede` for Chinese, `en-US-Chirp3-HD-Aoede` for English
- **Language storage**: `localStorage` with key `app-language`, default to `en`
- **Newsletter content**: Chinese newsletters supported; TTS follows UI language setting (not content auto-detect)

## Tasks

- [x] 🟩 **Step 1: Create i18n infrastructure**
  - [x] 🟩 Create `frontend/src/i18n/en.json` with all English strings (~100+ keys)
  - [x] 🟩 Create `frontend/src/i18n/zh.json` with Chinese translations
  - [x] 🟩 Create `frontend/src/i18n/LanguageContext.tsx` with `useLanguage` hook
  - [x] 🟩 Create `frontend/src/i18n/index.ts` exporting `t()` function and context

- [x] 🟩 **Step 2: Add language setting to UI**
  - [x] 🟩 Add language toggle section in `Settings.tsx` (dropdown: English / 中文)
  - [x] 🟩 Store language preference in `localStorage`
  - [x] 🟩 Wrap `App.tsx` with `LanguageProvider`

- [x] 🟩 **Step 3: Localize frontend components**
  - [x] 🟩 `IssueList.tsx` - headers, placeholders, status text, empty states
  - [x] 🟩 `Player.tsx` - error messages, loading states, toast messages
  - [x] 🟩 `AudioBar.tsx` - tooltips, voice status text
  - [x] 🟩 `SidePanel.tsx` - tab labels, status messages, placeholders
  - [x] 🟩 `Settings.tsx` - section headers, form labels, instructions
  - [x] 🟩 `Loading.tsx` - loading message
  - [x] 🟩 Date formatting - use locale-aware formatting

- [x] 🟩 **Step 4: Add bilingual voice command support**
  - [x] 🟩 Update `backend/voice_session.py` `COMMAND_WORDS` to include Chinese variants
  - [x] 🟩 Update `FILLER_WORDS` to include Chinese filler words
  - [x] 🟩 Update `_normalize_command_text()` to handle Chinese characters
  - [x] 🟩 Update `_detect_command()` to map Chinese commands to English action names

- [x] 🟩 **Step 5: Add language-aware TTS**
  - [x] 🟩 Add `language` field to `/ask-audio` endpoint request
  - [x] 🟩 Update `config.yaml` with Chinese TTS config (`cmn-CN-Chirp3-HD-Aoede`)
  - [x] 🟩 Update backend TTS service to select voice based on language parameter
  - [x] 🟩 Frontend: pass current language to Q&A API calls

- [x] 🟩 **Step 6: Localize AI prompts**
  - [x] 🟩 Add Chinese variants of `qaWithAudio` prompt in `config.yaml`
  - [x] 🟩 Add Chinese variants of `voiceMode` prompt in `config.yaml`
  - [x] 🟩 Update backend to select prompt based on language parameter

## Voice Command Translations

| English | Chinese | Pinyin |
|---------|---------|--------|
| play | 播放 | bōfàng |
| pause | 暂停 | zàntíng |
| next | 下一个 | xià yī gè |
| previous | 上一个 | shàng yī gè |
| bookmark | 收藏 | shōucáng |
| rewind | 后退 | hòutuì |
| forward | 快进 | kuàijìn |

## Testing (Required)

### Approach
Manual browser testing + API testing with curl

### Test Scenarios
- [x] 🟩 Language toggle in Settings switches all UI text immediately
- [x] 🟩 Language preference persists after page reload
- [x] 🟩 Voice command "播放" triggers play action
- [x] 🟩 Voice command "play" still works when UI is in Chinese
- [ ] 🟥 Q&A response is in Chinese when UI language is Chinese (requires live test)
- [ ] 🟥 TTS audio uses Chinese voice when UI is Chinese (requires live test)
- [x] 🟩 Date formatting shows Chinese format in Chinese mode

### Acceptance Criteria
- [x] All visible UI text changes when switching language
- [x] Both "play" and "播放" trigger the same playback action
- [x] Q&A answers match selected UI language (code verified)
- [x] TTS audio voice matches selected UI language (code verified)
- [x] No hardcoded English strings visible in Chinese mode
