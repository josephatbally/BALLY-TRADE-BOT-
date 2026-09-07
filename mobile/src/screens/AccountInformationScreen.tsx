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

type Props = NativeStackScreenProps<
  RootStackParamList,
  'AccountInformation'
>;

type InfoRowProps = {
  icon: string;
  title: string;
  value: string;
};

function InfoRow({icon, title, value}: InfoRowProps) {
  return (
    <View style={styles.infoRow}>
      <View style={styles.rowIcon}>
        <Text style={styles.rowIconText}>{icon}</Text>
      </View>

      <View style={styles.rowContent}>
        <Text style={styles.rowLabel}>{title}</Text>
        <Text style={styles.rowValue}>{value}</Text>
      </View>
    </View>
  );
}

function SectionHeader({title}: {title: string}) {
  return <Text style={styles.sectionTitle}>{title}</Text>;
}

export default function AccountInformationScreen({
  navigation,
  route,
}: Props) {
  const insets = useSafeAreaInsets();
  const user = route.params;

  const firstName =
    user.firstName?.trim() || 'Trader';

  const displayName =
    user.displayName?.trim() || firstName;

  const profileLetter =
    firstName.charAt(0).toUpperCase();

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <View style={styles.glowTop} />
      <View style={styles.glowBottom} />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.content,
          {
            paddingTop: Math.max(insets.top, 20),
            paddingBottom: Math.max(insets.bottom + 40, 40),
          },
        ]}>

        {/* HEADER */}

        <View style={styles.header}>
          <Pressable
            onPress={() => navigation.goBack()}
            style={({pressed}) => [
              styles.backButton,
              pressed && styles.backButtonPressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Go back">
            <Text style={styles.backArrow}>‹</Text>
          </Pressable>

          <View style={styles.headerText}>
            <Text style={styles.eyebrow}>BALLY FLOW</Text>

            <Text style={styles.title}>
              ACCOUNT
            </Text>

            <Text style={styles.subtitle}>
              Registered account information
            </Text>
          </View>

          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>
              ACTIVE
            </Text>
          </View>
        </View>

        {/* IDENTITY */}

        <View style={styles.identityCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {profileLetter}
            </Text>
          </View>

          <View style={styles.identityInfo}>
            <Text style={styles.identityLabel}>
              ACCOUNT HOLDER
            </Text>

            <Text style={styles.identityName}>
              {displayName}
            </Text>

            <Text style={styles.identityEmail}>
              {user.email}
            </Text>
          </View>
        </View>

        {/* PROFILE */}

        <SectionHeader title="PROFILE" />

        <View style={styles.sectionCard}>
          <InfoRow
            icon="N"
            title="DISPLAY NAME"
            value={displayName}
          />

          <View style={styles.divider} />

          <InfoRow
            icon="F"
            title="FIRST NAME"
            value={firstName}
          />

          <View style={styles.divider} />

          <InfoRow
            icon="@"
            title="EMAIL ADDRESS"
            value={user.email}
          />
        </View>

        {/* ACCOUNT */}

        <SectionHeader title="ACCOUNT" />

        <View style={styles.sectionCard}>
          <InfoRow
            icon="ID"
            title="ACCOUNT ID"
            value={user.id}
          />

          <View style={styles.divider} />

          <InfoRow
            icon="S"
            title="ACCOUNT STATUS"
            value="Authenticated"
          />

          <View style={styles.divider} />

          <InfoRow
            icon="A"
            title="ACCESS"
            value="BALLY FLOW account access enabled"
          />
        </View>

        {/* TRADING ACCOUNT */}

        <SectionHeader title="TRADING ACCOUNT" />

        <View style={styles.tradingCard}>
          <View style={styles.tradingHeader}>
            <View style={styles.tradingIcon}>
              <Text style={styles.tradingIconText}>
                MT5
              </Text>
            </View>

            <View style={styles.tradingInfo}>
              <Text style={styles.tradingTitle}>
                MT5 CONNECTION
              </Text>

              <Text style={styles.tradingSubtitle}>
                Broker connectivity is backend controlled
              </Text>
            </View>

            <View style={styles.notConnectedBadge}>
              <Text style={styles.notConnectedText}>
                PENDING
              </Text>
            </View>
          </View>

          <View style={styles.tradingDivider} />

          <Text style={styles.tradingDescription}>
            Broker credentials and trading connectivity are
            intentionally separated from the mobile account
            profile. The mobile application will receive
            connection status from the backend when the
            integration stage is implemented.
          </Text>
        </View>

        {/* SECURITY */}

        <SectionHeader title="ACCOUNT SECURITY" />

        <Pressable
          onPress={() =>
            navigation.navigate('Security', user)
          }
          style={({pressed}) => [
            styles.securityCard,
            pressed && styles.cardPressed,
          ]}>
          <View style={styles.securityIcon}>
            <Text style={styles.securityIconText}>
              S
            </Text>
          </View>

          <View style={styles.securityInfo}>
            <Text style={styles.securityTitle}>
              SECURITY SETTINGS
            </Text>

            <Text style={styles.securityText}>
              Manage authentication and account protection
            </Text>
          </View>

          <Text style={styles.securityArrow}>
            ›
          </Text>
        </Pressable>

        {/* NOTICE */}

        <View style={styles.noticeCard}>
          <View style={styles.noticeIcon}>
            <Text style={styles.noticeIconText}>
              !
            </Text>
          </View>

          <View style={styles.noticeContent}>
            <Text style={styles.noticeTitle}>
              ACCOUNT DATA
            </Text>

            <Text style={styles.noticeText}>
              Profile information shown here comes from the
              authenticated navigation state. Persistent
              account synchronization will be connected to
              the backend authentication and database layer
              during integration.
            </Text>
          </View>
        </View>

        {/* FOOTER */}

        <View style={styles.footer}>
          <View style={styles.footerDot} />

          <Text style={styles.footerText}>
            BALLY FLOW ACCOUNT INFORMATION
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

  content: {
    paddingHorizontal: 18,
  },

  glowTop: {
    position: 'absolute',
    width: 330,
    height: 330,
    borderRadius: 165,
    backgroundColor: '#111B5B',
    opacity: 0.15,
    top: -190,
    right: -120,
  },

  glowBottom: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: '#15204B',
    opacity: 0.11,
    bottom: -150,
    left: -150,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 23,
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
    marginRight: 11,
    marginTop: 5,
  },

  backButtonPressed: {
    backgroundColor: '#111A2A',
  },

  backArrow: {
    color: '#A8B2C7',
    fontSize: 28,
    fontWeight: '300',
    lineHeight: 30,
  },

  headerText: {
    flex: 1,
  },

  eyebrow: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 2.1,
    marginBottom: 7,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  subtitle: {
    color: '#69758E',
    fontSize: 10,
    marginTop: 6,
  },

  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D211A',
    borderRadius: 20,
    paddingHorizontal: 9,
    paddingVertical: 7,
    marginTop: 8,
    marginLeft: 8,
  },

  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  statusText: {
    color: '#35E68A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  identityCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 20,
    padding: 17,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 26,
  },

  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#111A38',
    borderWidth: 1,
    borderColor: '#334BFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },

  avatarText: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '900',
  },

  identityInfo: {
    flex: 1,
  },

  identityLabel: {
    color: '#7083FF',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
  },

  identityName: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '900',
    marginTop: 5,
  },

  identityEmail: {
    color: '#68748B',
    fontSize: 9,
    marginTop: 4,
  },

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 1.6,
    marginBottom: 9,
    marginTop: 2,
  },

  sectionCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    overflow: 'hidden',
    marginBottom: 25,
  },

  infoRow: {
    minHeight: 72,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
  },

  rowIcon: {
    width: 36,
    height: 36,
    borderRadius: 11,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  rowIconText: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
  },

  rowContent: {
    flex: 1,
  },

  rowLabel: {
    color: '#647087',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  rowValue: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
    marginTop: 5,
  },

  divider: {
    height: 1,
    backgroundColor: '#172032',
    marginLeft: 62,
  },

  tradingCard: {
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#1C2949',
    borderRadius: 18,
    padding: 16,
    marginBottom: 25,
  },

  tradingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  tradingIcon: {
    width: 45,
    height: 45,
    borderRadius: 13,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  tradingIconText: {
    color: '#7083FF',
    fontSize: 9,
    fontWeight: '900',
  },

  tradingInfo: {
    flex: 1,
  },

  tradingTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.3,
  },

  tradingSubtitle: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  notConnectedBadge: {
    backgroundColor: '#20191B',
    borderRadius: 16,
    paddingHorizontal: 8,
    paddingVertical: 6,
    marginLeft: 7,
  },

  notConnectedText: {
    color: '#FFB36B',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  tradingDivider: {
    height: 1,
    backgroundColor: '#1C2949',
    marginVertical: 14,
  },

  tradingDescription: {
    color: '#78859D',
    fontSize: 8,
    lineHeight: 15,
  },

  securityCard: {
    minHeight: 75,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 18,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 25,
  },

  cardPressed: {
    backgroundColor: '#0E1423',
  },

  securityIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  securityIconText: {
    color: '#7083FF',
    fontSize: 11,
    fontWeight: '900',
  },

  securityInfo: {
    flex: 1,
  },

  securityTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
  },

  securityText: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  securityArrow: {
    color: '#65718A',
    fontSize: 24,
    fontWeight: '300',
    marginLeft: 8,
  },

  noticeCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 17,
    padding: 15,
    flexDirection: 'row',
    marginBottom: 24,
  },

  noticeIcon: {
    width: 30,
    height: 30,
    borderRadius: 10,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  noticeIconText: {
    color: '#7083FF',
    fontSize: 12,
    fontWeight: '900',
  },

  noticeContent: {
    flex: 1,
  },

  noticeTitle: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1,
    marginBottom: 6,
  },

  noticeText: {
    color: '#68748B',
    fontSize: 8,
    lineHeight: 15,
  },

  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },

  footerDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  footerText: {
    color: '#46526A',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.7,
  },
});
