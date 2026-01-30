import { useLanguage } from '../i18n'
import './Loading.css'

interface LoadingProps {
  message?: string
}

export default function Loading({ message }: LoadingProps) {
  const { t } = useLanguage()
  const displayMessage = message ?? t('common.loading')
  return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <p className="loading-message">{displayMessage}</p>
    </div>
  )
}
