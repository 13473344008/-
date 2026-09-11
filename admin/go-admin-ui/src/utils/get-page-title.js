import storage from '@/utils/storage'
import settings from '@/settings'

export function getAppName(name) {
  return !name || /^(?:go[ -]?admin)(?:\s*(?:后台)?管理系统)?$/i.test(name) ? settings.title : name
}

export default function getPageTitle(pageTitle) {
  const app_info = storage.get('app_info')
  const title = getAppName(app_info?.sys_app_name)
  if (pageTitle) {
    return `${pageTitle} - ${title}`
  }
  return `${title}`
}
