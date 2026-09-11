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

/**
 * Chinese, the default and the fallback.
 *
 * There is deliberately no menu.ts or dict.ts here. Those two translate text
 * that arrives from the database, which is already Chinese -- a zh-CN copy
 * would be a second source of truth for the same strings, and the two would
 * drift the first time someone renamed a menu. Chinese always falls through to
 * the database value; see lang/backend.ts.
 */
import traffic from './traffic'

export default {
  traffic,
  passportPreview,
  passportMedia, passportHistory, passportPublish, passportReview, passportSections, passportBatch, passport, common, schedule, devTools, demo, sysTools, profile, layout, route, components, login, dashboard, admin, composables }
