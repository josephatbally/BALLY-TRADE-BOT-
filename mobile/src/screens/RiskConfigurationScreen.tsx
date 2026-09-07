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

type Props = NativeStackScreenProps<
  RootStackParamList,
  'RiskConfiguration'
>;

type RiskItemProps = {
  label: string;
  value: string;
  description: string;
};

export default function RiskConfigurationScreen({
  navigation,
}: Props) {
  const insets = useSafeAreaInsets();

  const handleBack = () => {
    navigation.goBack();
  };

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
            paddingTop: Math.max(insets.top, 18),
            paddingBottom: Math.max(insets.bottom + 40, 40),
          },
        ]}>

        {/* HEADER */}
        <View style={styles.header}>
          <Pressable
            onPress={handleBack}
            style={({pressed}) => [
              styles.backButton,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Go back">
            <Text style={styles.backIcon}>‹</Text>
          </Pressable>

          <View style={styles.headerContent}>
            <Text style={styles.appName}>
              {BRANDING.appName}
            </Text>

            <Text style={styles.title}>
              RISK CONFIGURATION
            </Text>

            <Text style={styles.subtitle}>
              Backend-controlled trading risk management
            </Text>
          </View>

          <View style={styles.secureBadge}>
            <View style={styles.secureDot} />
            <Text style={styles.secureText}>SECURE</Text>
          </View>
        </View>

        {/* INTRO */}
        <View style={styles.introCard}>
          <View style={styles.introIcon}>
            <Text style={styles.introIconText}>R</Text>
          </View>

          <View style={styles.introContent}>
            <Text style={styles.introTitle}>
              RISK MANAGEMENT
            </Text>

            <Text style={styles.introText}>
              Risk parameters are controlled by the BALLY
              TRADES BOT backend. The mobile application
              displays the active risk configuration without
              bypassing backend validation.
            </Text>
          </View>
        </View>

        {/* ACTIVE PROFILE */}
        <Text style={styles.sectionTitle}>
          ACTIVE RISK PROFILE
        </Text>

        <View style={styles.profileCard}>
          <View style={styles.profileHeader}>
            <View>
              <Text style={styles.profileTitle}>
                STANDARD RISK
              </Text>

              <Text style={styles.profileSubtitle}>
                Current backend risk configuration
              </Text>
            </View>

            <View style={styles.activeBadge}>
              <View style={styles.activeDot} />
              <Text style={styles.activeText}>
                ACTIVE
              </Text>
            </View>
          </View>

          <View style={styles.profileDivider} />

          <View style={styles.profileRow}>
            <View>
              <Text style={styles.profileLabel}>
                DEFAULT RISK
              </Text>
              <Text style={styles.profileDescription}>
                Default percentage risk per trade
              </Text>
            </View>

            <Text style={styles.profileValue}>
              1.0%
            </Text>
          </View>
        </View>

        {/* RISK PARAMETERS */}
        <Text style={styles.sectionTitle}>
          RISK PARAMETERS
        </Text>

        <View style={styles.parametersCard}>
          <RiskItem
            label="DEFAULT RISK"
            value="1.0%"
            description="Backend default risk percentage"
          />

          <View style={styles.divider} />

          <RiskItem
            label="RISK / REWARD"
            value="3.0 : 1"
            description="Configured trading risk-to-reward target"
          />

          <View style={styles.divider} />

          <RiskItem
            label="POSITION SIZING"
            value="BACKEND"
            description="Calculated and validated by the execution pipeline"
          />

          <View style={styles.divider} />

          <RiskItem
            label="MARGIN CHECK"
            value="REQUIRED"
            description="Available margin must pass backend validation"
          />

          <View style={styles.divider} />

          <RiskItem
            label="BROKER LIMITS"
            value="ENFORCED"
            description="Broker volume and execution constraints apply"
          />
        </View>

        {/* SAFETY */}
        <Text style={styles.sectionTitle}>
          EXECUTION SAFETY
        </Text>

        <View style={styles.safetyCard}>
          <View style={styles.safetyHeader}>
            <View style={styles.safetyIcon}>
              <Text style={styles.safetyIconText}>✓</Text>
            </View>

            <View style={styles.safetyHeaderContent}>
              <Text style={styles.safetyTitle}>
                BACKEND VALIDATION REQUIRED
              </Text>

              <Text style={styles.safetySubtitle}>
                Mobile settings cannot bypass execution controls
              </Text>
            </View>
          </View>

          <View style={styles.safetyList}>
            <SafetyRow text="Risk limits validated before execution" />
            <SafetyRow text="Lot size validated against broker limits" />
            <SafetyRow text="Margin availability checked before order submission" />
            <SafetyRow text="Stop distance and trade plan validated" />
            <SafetyRow text="Execution layer remains authoritative" />
          </View>
        </View>

        {/* INFORMATION */}
        <View style={styles.infoCard}>
          <View style={styles.infoIcon}>
            <Text style={styles.infoIconText}>i</Text>
          </View>

          <View style={styles.infoContent}>
            <Text style={styles.infoTitle}>
              IMPORTANT
            </Text>

            <Text style={styles.infoText}>
              Risk configuration is intentionally separated
              from the mobile user interface. Any future
              adjustable risk controls must be validated by
              the backend before becoming active.
            </Text>
          </View>
        </View>

        {/* FOOTER */}
        <View style={styles.footer}>
          <View style={styles.footerDot} />

          <Text style={styles.footerText}>
            BALLY FLOW • BACKEND RISK CONTROL
          </Text>
        </View>

      </ScrollView>
    </View>
  );
}

function RiskItem({
  label,
  value,
  description,
}: RiskItemProps) {
  return (
    <View style={styles.parameterRow}>
      <View style={styles.parameterContent}>
        <Text style={styles.parameterLabel}>
          {label}
        </Text>

        <Text style={styles.parameterDescription}>
          {description}
        </Text>
      </View>

      <View style={styles.parameterValueBox}>
        <Text style={styles.parameterValue}>
          {value}
        </Text>
      </View>
    </View>
  );
}

function SafetyRow({text}: {text: string}) {
  return (
    <View style={styles.safetyRow}>
      <View style={styles.safetyCheck}>
        <Text style={styles.safetyCheckText}>✓</Text>
      </View>

      <Text style={styles.safetyRowText}>
        {text}
      </Text>
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
    opacity: 0.16,
    top: -190,
    right: -120,
  },

  glowBottom: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: '#15204B',
    opacity: 0.12,
    bottom: -150,
    left: -150,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 24,
  },

  backButton: {
    width: 40,
    height: 40,
    borderRadius: 13,
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
    marginTop: 5,
  },

  backIcon: {
    color: '#7083FF',
    fontSize: 30,
    fontWeight: '300',
    lineHeight: 32,
    marginTop: -2,
  },

  headerContent: {
    flex: 1,
  },

  appName: {
    color: '#7083FF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 2.2,
    marginBottom: 7,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '900',
    letterSpacing: 0.2,
  },

  subtitle: {
    color: '#69758E',
    fontSize: 10,
    lineHeight: 15,
    marginTop: 6,
  },

  secureBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111A38',
    borderRadius: 20,
    paddingHorizontal: 8,
    paddingVertical: 7,
    marginTop: 8,
    marginLeft: 7,
  },

  secureDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 6,
  },

  secureText: {
    color: '#35E68A',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  introCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 16,
    flexDirection: 'row',
    marginBottom: 27,
  },

  introIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  introIconText: {
    color: '#7083FF',
    fontSize: 15,
    fontWeight: '900',
  },

  introContent: {
    flex: 1,
  },

  introTitle: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  introText: {
    color: '#69758E',
    fontSize: 9,
    lineHeight: 15,
    marginTop: 5,
  },

  sectionTitle: {
    color: '#A8B2C7',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1.6,
    marginBottom: 10,
    marginTop: 4,
  },

  profileCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1C2949',
    borderRadius: 19,
    padding: 16,
    marginBottom: 25,
  },

  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  profileTitle: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  profileSubtitle: {
    color: '#647087',
    fontSize: 8,
    marginTop: 4,
  },

  activeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0D211A',
    borderRadius: 9,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },

  activeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#35E68A',
    marginRight: 5,
  },

  activeText: {
    color: '#35E68A',
    fontSize: 6,
    fontWeight: '900',
    letterSpacing: 0.7,
  },

  profileDivider: {
    height: 1,
    backgroundColor: '#172032',
    marginVertical: 15,
  },

  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  profileLabel: {
    color: '#69758E',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  profileDescription: {
    color: '#59657B',
    fontSize: 7,
    marginTop: 4,
  },

  profileValue: {
    color: '#7083FF',
    fontSize: 22,
    fontWeight: '900',
  },

  parametersCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    paddingHorizontal: 15,
    marginBottom: 25,
  },

  parameterRow: {
    minHeight: 72,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  parameterContent: {
    flex: 1,
    paddingRight: 10,
  },

  parameterLabel: {
    color: '#C4CCDA',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  parameterDescription: {
    color: '#59657B',
    fontSize: 7,
    lineHeight: 12,
    marginTop: 4,
  },

  parameterValueBox: {
    backgroundColor: '#111A38',
    borderWidth: 1,
    borderColor: '#27345C',
    borderRadius: 9,
    paddingHorizontal: 9,
    paddingVertical: 7,
  },

  parameterValue: {
    color: '#7083FF',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.5,
  },

  divider: {
    height: 1,
    backgroundColor: '#172032',
  },

  safetyCard: {
    backgroundColor: '#0A0E18',
    borderWidth: 1,
    borderColor: '#1B2435',
    borderRadius: 19,
    padding: 15,
    marginBottom: 25,
  },

  safetyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  safetyIcon: {
    width: 39,
    height: 39,
    borderRadius: 12,
    backgroundColor: '#0D211A',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 11,
  },

  safetyIconText: {
    color: '#35E68A',
    fontSize: 17,
    fontWeight: '900',
  },

  safetyHeaderContent: {
    flex: 1,
  },

  safetyTitle: {
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.6,
  },

  safetySubtitle: {
    color: '#59657B',
    fontSize: 7,
    marginTop: 4,
  },

  safetyList: {
    marginTop: 15,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: '#172032',
  },

  safetyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },

  safetyCheck: {
    width: 17,
    height: 17,
    borderRadius: 6,
    backgroundColor: '#101A19',
    borderWidth: 1,
    borderColor: '#244F3C',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 9,
  },

  safetyCheckText: {
    color: '#35E68A',
    fontSize: 9,
    fontWeight: '900',
  },

  safetyRowText: {
    flex: 1,
    color: '#69758E',
    fontSize: 8,
    lineHeight: 13,
  },

  infoCard: {
    backgroundColor: '#0B1020',
    borderWidth: 1,
    borderColor: '#1C2949',
    borderRadius: 17,
    padding: 14,
    flexDirection: 'row',
    marginBottom: 24,
  },

  infoIcon: {
    width: 31,
    height: 31,
    borderRadius: 10,
    backgroundColor: '#111A38',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },

  infoIconText: {
    color: '#7083FF',
    fontSize: 12,
    fontWeight: '900',
  },

  infoContent: {
    flex: 1,
  },

  infoTitle: {
    color: '#A8B2C7',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.8,
  },

  infoText: {
    color: '#59657B',
    fontSize: 7,
    lineHeight: 13,
    marginTop: 5,
  },

  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },

  footerDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#7083FF',
    marginRight: 6,
  },

  footerText: {
    color: '#46526A',
    fontSize: 7,
    fontWeight: '800',
    letterSpacing: 0.8,
  },

  pressed: {
    opacity: 0.78,
    transform: [
      {
        scale: 0.985,
      },
    ],
  },
});
