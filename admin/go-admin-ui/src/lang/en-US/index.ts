import passportMedia from './passport/media'
import passportPreview from './passport/preview'
import passportHistory from './passport/history'
import passportPublish from './passport/publication'
import passportReview from './passport/reviews'
import passportSections from './passport/sections'
import passportBatch from './passport/batches'
import passport from './passport'
import common from './common'
import layout from './layout'
import profile from './profile'
import sysTools from './sys-tools'
import demo from './demo'
import devTools from './dev-tools'
import schedule from './schedule'
import route from './route'
import components from './components'
import login from './login'
import dashboard from './dashboard'
import admin from './admin'
import composables from './composables'
import menu from './menu'
import dict from './dict'

/**
 * English.
 *
 * Unlike zh-CN this does carry menu and dict: those are the translations of
 * text the backend only ever sends in Chinese.
 */
import traffic from './traffic'

export default {
  traffic,
  passportPreview,
  passportMedia, passportHistory, passportPublish, passportReview, passportSections, passportBatch, passport, common, schedule, devTools, demo, sysTools, profile, layout, route, components, login, dashboard, admin, composables, menu, dict }
