import React from 'react';
import {
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useSafeAreaInsets} from 'react-native-safe-area-context';

import {RootStackParamList} from '../navigation/navigationTypes';
import {BRANDING} from '../config/branding';

type NotificationsScreenProps = NativeStackScreenProps<
  RootStackParamList,
  'Notifications'
>;

type NotificationType =
  | 'SYSTEM'
  | 'TRADING'
  | 'MARKET'
  | 'ACCOUNT'
  | 'SECURITY';

type NotificationRecord = {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  createdAt: string;
  read: boolean;
};

type NotificationFilter = 'ALL' | 'UNREAD';

function TypeBadge({
  type,
}: {
  type: NotificationType;
}) {
  const label =
    type === 'TRADING'
      ? 'TRADING'
      : type === 'MARKET'
      ? 'MARKET'
      : type === 'ACCOUNT'
      ? 'ACCOUNT'
      : type === 'SECURITY'
      ? 'SECURITY'
      : 'SYSTEM';

  return (
    <View
      style={[
        styles.typeBadge,
        type === 'TRADING' && styles.tradingBadge,
        type === 'MARKET' && styles.marketBadge,
        type === 'ACCOUNT' && styles.accountBadge,
        type === 'SECURITY' && styles.securityBadge,
        type === 'SYSTEM' && styles.systemBadge,
      ]}>
      <Text
        style={[
          styles.typeBadgeText,
          type === 'TRADING' && styles.tradingText,
          type === 'MARKET' && styles.marketText,
          type === 'ACCOUNT' && styles.accountText,
          type === 'SECURITY' && styles.securityText,
          type === 'SYSTEM' && styles.systemText,
        ]}>
        {label}
      </Text>
    </View>
  );
}

function NotificationCard({
  notification,
}: {
  notification: NotificationRecord;
}) {
  return (
    <View
      style={[
        styles.notificationCard,
        !notification.read && styles.notificationUnread,
      ]}>
      <View style={styles.notificationHeader}>
        <View style={styles.notificationTitleRow}>
          {!notification.read && (
            <View style={styles.unreadDot} />
          )}

          <Text style={styles.notificationTitle}>
            {notification.title}
          </Text>
        </View>

        <TypeBadge type={notification.type} />
      </View>

      <Text style={styles.notificationMessage}>
        {notification.message}
      </Text>

      <Text style={styles.notificationDate}>
        {notification.createdAt}
      </Text>
    </View>
  );
}

export default function NotificationsScreen({
  route,
  navigation,
}: NotificationsScreenProps) {
  const insets = useSafeAreaInsets();

  const user = route.params;

  /*
   * ============================================================
   * BACKEND NOTIFICATION DATA
   * ============================================================
   *
   * This array is intentionally empty.
   *
   * Notifications must eventually be retrieved from the
   * authenticated BALLY TRADES BOT backend.
   *
   * The backend/admin system will control:
   *
   * - notification title
   * - notification message
   * - notification type
   * - publication time
   * - read/unread state
   * - targeted users
   * - system/trading/market/account/security alerts
   *
   * Do NOT replace this with permanent hardcoded notifications.
   */
  const [notifications] = React.useState<
    NotificationRecord[]
  >([]);

  const [filter, setFilter] =
    React.useState<NotificationFilter>('ALL');

  const unreadCount = notifications.filter(
    notification => !notification.read,
  ).length;

  const visibleNotifications =
    filter === 'UNREAD'
      ? notifications.filter(
          notification => !notification.read,
        )
      : notifications;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.scrollContent,
          {
            paddingTop: Math.max(
              insets.top,
              20,
            ),
            paddingBottom: Math.max(
              insets.bottom + 40,
              30,
            ),
          },
        ]}>

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={styles.backButton}>
            <Text style={styles.backText}>
              ‹
            </Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.appName}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.title}>
              NOTIFICATIONS
            </Text>

            <Text style={styles.subtitle}>
              {user.firstName} • System and trading updates
            </Text>
          </View>
        </View>

        {/* ================================================= */}
        {/* NOTIFICATION STATUS */}
        {/* ================================================= */}

        <View style={styles.statusCard}>
          <View style={styles.statusIcon}>
            <Text style={styles.statusIconText}>
              !
            </Text>
          </View>

          <View style={styles.statusContent}>
            <Text style={styles.statusTitle}>
              NOTIFICATION CENTER
            </Text>

            <Text style={styles.statusText}>
              {notifications.length === 0
                ? 'Waiting for notifications from the BALLY FLOW backend.'
                : `${notifications.length} notification${
                    notifications.length === 1
                      ? ''
                      : 's'
                  } available.`}
            </Text>
          </View>

          {unreadCount > 0 && (
            <View style={styles.unreadCount}>
              <Text style={styles.unreadCountText}>
                {unreadCount}
              </Text>
            </View>
          )}
        </View>

        {/* ================================================= */}
        {/* FILTER */}
        {/* ================================================= */}

        <View style={styles.filterContainer}>
          <Pressable
            onPress={() => setFilter('ALL')}
            style={[
              styles.filterButton,
              filter === 'ALL' &&
                styles.filterButtonActive,
            ]}>
            <Text
              style={[
                styles.filterText,
                filter === 'ALL' &&
                  styles.filterTextActive,
              ]}>
              ALL
            </Text>
          </Pressable>

          <Pressable
            onPress={() => setFilter('UNREAD')}
            style={[
              styles.filterButton,
              filter === 'UNREAD' &&
                styles.filterButtonActive,
            ]}>
            <Text
              style={[
                styles.filterText,
                filter === 'UNREAD' &&
                  styles.filterTextActive,
              ]}>
              UNREAD
            </Text>

            {unreadCount > 0 && (
              <View style={styles.filterCount}>
                <Text style={styles.filterCountText}>
                  {unreadCount}
                </Text>
              </View>
            )}
          </Pressable>
        </View>

        {/* ================================================= */}
        {/* FEED */}
        {/* ================================================= */}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            NOTIFICATION FEED
          </Text>

          <Text style={styles.sectionMeta}>
            BACKEND CONTROLLED
          </Text>
        </View>

        {visibleNotifications.length === 0 ? (
          <View style={styles.emptyCard}>
            <View style={styles.emptyIcon}>
              <Text style={styles.emptyIconText}>
                ✓
              </Text>
            </View>

            <Text style={styles.emptyTitle}>
              NO NOTIFICATIONS
            </Text>

            <Text style={styles.emptyText}>
              {filter === 'UNREAD'
                ? 'There are currently no unread notifications.'
                : 'Notifications published by the BALLY FLOW administration and trading backend will appear here.'}
            </Text>
          </View>
        ) : (
          visibleNotifications.map(notification => (
            <NotificationCard
              key={notification.id}
              notification={notification}
            />
          ))
        )}

        {/* ================================================= */}
        {/* ADMIN / BACKEND NOTICE */}
        {/* ================================================= */}

        <View style={styles.adminNotice}>
          <View style={styles.adminNoticeHeader}>
            <View style={styles.adminNoticeDot} />

            <Text style={styles.adminNoticeTitle}>
              SERVER CONTROLLED
            </Text>
          </View>

          <Text style={styles.adminNoticeText}>
            Notification content is not permanently stored
            inside the mobile interface. Authorized BALLY
            FLOW administrators can publish system, market,
            trading, account and security notifications
            through the backend.
          </Text>
        </View>

        {/* ================================================= */}
        {/* FOOTER */}
        {/* ================================================= */}

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            BALLY FLOW NOTIFICATION SERVICE
          </Text>
        </View>

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#05070D',
  },

  scrollContent: {
    paddingHorizontal: 18,
  },

  glowTop: {
    position: 'absolute',
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: '#111B5B',
    opacity: 0.16,
    top: -190,
    right: -110,
  },

  glowBottom: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: '#15204B',
    opacity: 0.12,
    bottom: -130,
    left: -130,
  },

  /* HEADER */

  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 25,
  },

  backButton: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 5,
  },

  backText: {
    color: '#FFFFFF',
    fontSize: 28,
    lineHeight: 30,
    fontWeight: '300',
  },

  headerText: {
    flex: 1,
  },

  appName: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 2,
    marginBottom: 6,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 25,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  subtitle: {
    color: '#69758E',
    fontSize: 10,
    marginTop: 6,
  },

  /* STATUS */

  statusCard: {
    minHeight: 86,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },

  statusIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#11182A',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  statusIconText: {
    color: '#7083FF',
    fontSize: 17,
    fontWeight: '900',
  },

  statusContent: {
    flex: 1,
  },

  statusTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  statusText: {
    color: '#647087',
    fontSize: 8,
    lineHeight: 14,
    marginTop: 5,
  },

  unreadCount: {
    minWidth: 27,
    height: 27,
    borderRadius: 14,
    backgroundColor: '#7083FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },

  unreadCountText: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
  },

  /* FILTER */

  filterContainer: {
    flexDirection: 'row',
    backgroundColor: '#0A0E18',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1B2435',
    padding: 4,
    marginBottom: 25,
  },

  filterButton: {
    flex: 1,
    minHeight: 35,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },

  filterButtonActive: {
    backgroundColor: '#11182A',
  },

  filterText: {
    color: '#56627A',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  filterTextActive: {
    color: '#FFFFFF',
  },

  filterCount: {
    minWidth: 17,
    height: 17,
    borderRadius: 9,
    backgroundColor: '#7083FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 6,
  },

  filterCountText: {
    color: '#FFFFFF',
    fontSize: 7,
    fontWeight: '900',
  },

  /* SECTION */

  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 11,
  },

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.5,
  },

  sectionMeta: {
    color: '#56627A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  /* EMPTY */

  emptyCard: {
    minHeight: 205,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 30,
  },

  emptyIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#11182A',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 13,
  },

  emptyIconText: {
    color: '#7083FF',
    fontSize: 19,
    fontWeight: '900',
  },

  emptyTitle: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  emptyText: {
    color: '#647087',
    fontSize: 9,
    lineHeight: 16,
    textAlign: 'center',
    marginTop: 8,
  },

  /* NOTIFICATION CARD */

  notificationCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 16,
    padding: 14,
    marginBottom: 10,
  },

  notificationUnread: {
    borderColor: '#28365B',
  },

  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },

  notificationTitleRow: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: 10,
  },

  unreadDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 7,
  },

  notificationTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    flex: 1,
  },

  typeBadge: {
    borderRadius: 6,
    paddingHorizontal: 7,
    paddingVertical: 4,
  },

  typeBadgeText: {
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  tradingBadge: {
    backgroundColor: '#0D211A',
  },

  tradingText: {
    color: '#35E68A',
  },

  marketBadge: {
    backgroundColor: '#11182A',
  },

  marketText: {
    color: '#7083FF',
  },

  accountBadge: {
    backgroundColor: '#171B23',
  },

  accountText: {
    color: '#A8B2C7',
  },

  securityBadge: {
    backgroundColor: '#281419',
  },

  securityText: {
    color: '#FF7185',
  },

  systemBadge: {
    backgroundColor: '#151923',
  },

  systemText: {
    color: '#8995B1',
  },

  notificationMessage: {
    color: '#8995AE',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 12,
  },

  notificationDate: {
    color: '#56627A',
    fontSize: 7,
    marginTop: 11,
  },

  /* ADMIN NOTICE */

  adminNotice: {
    marginTop: 15,
    backgroundColor: '#0B1020',
    borderRadius: 12,
    padding: 13,
  },

  adminNoticeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 7,
  },

  adminNoticeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 7,
  },

  adminNoticeTitle: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  adminNoticeText: {
    color: '#66738C',
    fontSize: 8,
    lineHeight: 14,
  },

  /* FOOTER */

  footer: {
    alignItems: 'center',
    marginTop: 22,
  },

  footerText: {
    color: '#46526A',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
});

