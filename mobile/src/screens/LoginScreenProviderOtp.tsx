import React, {useMemo, useState} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {ActivityIndicator, Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View} from 'react-native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {initiateLogin, initiateRegistration, resendSecurityCode, verifySecurityCode} from '../api/authApi';
import {RootStackParamList, AuthenticatedUser} from '../navigation/navigationTypes';

type Props = NativeStackScreenProps<RootStackParamList, 'Login'>;
type Channel = 'email' | 'sms' | 'whatsapp';

const CHANNELS: {key: Channel; label: string; icon: string}[] = [
  {key: 'email', label: 'Email', icon: '✉'},
  {key: 'sms', label: 'SMS', icon: '▣'},
  {key: 'whatsapp', label: 'WhatsApp', icon: '◉'},
];

export default function LoginScreenProviderOtp({navigation}: Props) {
  const [mode, setMode] = useState<'signin' | 'register'>('signin');
  const [step, setStep] = useState<'credentials' | 'otp'>('credentials');
  const [channel, setChannel] = useState<Channel>('email');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [activeIdentifier, setActiveIdentifier] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendSeconds, setResendSeconds] = useState(30);
  const [devHintCode, setDevHintCode] = useState<string | null>(null);

  const destinationHint = useMemo(() => {
    if (channel === 'email') return mode === 'register' ? email : identifier;
    return phone || identifier;
  }, [channel, mode, email, phone, identifier]);

  const sendCode = async () => {
    if (mode === 'register') {
      if (!name.trim()) return Alert.alert('Missing name', 'Enter your full name.');
      if (!/^\S+@\S+\.\S+$/.test(email.trim())) return Alert.alert('Invalid email', 'Enter a valid email address.');
      if (phone.trim().length < 5) return Alert.alert('Invalid phone', 'Enter your mobile phone number.');
    } else if (!identifier.trim()) {
      return Alert.alert('Input required', 'Enter your registered email or phone number.');
    }

    setLoading(true);
    try {
      const res = mode === 'register'
        ? await initiateRegistration({full_name: name.trim(), email: email.trim().toLowerCase(), phone: phone.trim(), country_code: '+255', channel})
        : await initiateLogin({identifier: identifier.trim(), channel});

      if (res.verification_required === false && res.token && res.user) {
        const user: AuthenticatedUser = {
          id: String(res.user.id),
          email: res.user.email,
          firstName: (res.user.full_name || 'Trader').split(' ')[0],
          displayName: res.user.full_name,
          phone: res.user.phone,
          countryCode: res.user.country_code,
          token: res.token,
        };
        await AsyncStorage.setItem('@bally_auth_token', res.token);
        await AsyncStorage.setItem('@bally_auth_user', JSON.stringify(user));
        navigation.replace('MainTabs', user);
        return;
      }

      const destination = res.identifier || destinationHint;
      setActiveIdentifier(destination);
      setDevHintCode(res.dev_code || null);
      setCode('');
      setStep('otp');
      setResendSeconds(30);
      Alert.alert('Code sent', `A verification code was sent by ${channel} to ${destination}.`);
    } catch (err: any) {
      Alert.alert('Verification unavailable', err?.message || 'Unable to send the verification code.');
    } finally {
      setLoading(false);
    }
  };

  const verify = async () => {
    if (!/^\d{6}$/.test(code.trim())) return Alert.alert('Invalid code', 'Enter the 6-digit code you received.');
    setLoading(true);
    try {
      const res = await verifySecurityCode({identifier: activeIdentifier.trim().toLowerCase(), code: code.trim()});
      const user: AuthenticatedUser = {
        id: String(res.user.id),
        email: res.user.email,
        firstName: (res.user.full_name || 'Trader').split(' ')[0],
        displayName: res.user.full_name,
        phone: res.user.phone,
        countryCode: res.user.country_code,
      };
      navigation.replace('MainTabs', user);
    } catch (err: any) {
      Alert.alert('Verification failed', err?.message || 'The code is invalid or expired.');
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    if (resendSeconds > 0) return;
    setLoading(true);
    try {
      const res = await resendSecurityCode({identifier: activeIdentifier, channel});
      setDevHintCode(res.dev_code || null);
      setResendSeconds(30);
      Alert.alert('Code resent', `A new verification code was sent by ${channel}.`);
    } catch (err: any) {
      Alert.alert('Resend failed', err?.message || 'Unable to resend the code.');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (step !== 'otp' || resendSeconds <= 0) return;
    const timer = setInterval(() => setResendSeconds(v => Math.max(0, v - 1)), 1000);
    return () => clearInterval(timer);
  }, [step, resendSeconds]);

  return (
    <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.brand}>BALLY FLOW</Text>
        <Text style={styles.tagline}>EXECUTE YOUR EDGE</Text>
        <View style={styles.card}>
          {step === 'credentials' ? <>
            <View style={styles.tabs}>
              <TouchableOpacity style={[styles.tab, mode === 'signin' && styles.activeTab]} onPress={() => setMode('signin')}><Text style={styles.tabText}>Sign In</Text></TouchableOpacity>
              <TouchableOpacity style={[styles.tab, mode === 'register' && styles.activeTab]} onPress={() => setMode('register')}><Text style={styles.tabText}>Create Account</Text></TouchableOpacity>
            </View>

            <Text style={styles.title}>{mode === 'register' ? 'Create your account' : 'Welcome back'}</Text>
            <Text style={styles.subtitle}>Choose where BALLY FLOW should send your verification code.</Text>

            {mode === 'register' && <>
              <Text style={styles.label}>FULL NAME</Text>
              <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Full name" placeholderTextColor="#64748B" />
              <Text style={styles.label}>EMAIL ADDRESS</Text>
              <TextInput style={styles.input} value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" placeholder="you@example.com" placeholderTextColor="#64748B" />
              <Text style={styles.label}>PHONE NUMBER</Text>
              <TextInput style={styles.input} value={phone} onChangeText={setPhone} keyboardType="phone-pad" placeholder="712 345 678" placeholderTextColor="#64748B" />
            </>}

            {mode === 'signin' && <>
              <Text style={styles.label}>REGISTERED EMAIL OR PHONE</Text>
              <TextInput style={styles.input} value={identifier} onChangeText={setIdentifier} autoCapitalize="none" placeholder="Email or phone" placeholderTextColor="#64748B" />
            </>}

            <Text style={styles.label}>VERIFICATION METHOD</Text>
            <View style={styles.channels}>
              {CHANNELS.map(item => (
                <TouchableOpacity key={item.key} style={[styles.channel, channel === item.key && styles.channelActive]} onPress={() => setChannel(item.key)}>
                  <Text style={styles.channelIcon}>{item.icon}</Text>
                  <Text style={styles.channelText}>{item.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity style={styles.button} onPress={sendCode} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>{mode === 'register' ? 'CREATE ACCOUNT & SEND CODE' : 'SEND VERIFICATION CODE'}</Text>}
            </TouchableOpacity>
          </> : <>
            <Text style={styles.title}>Verify your account</Text>
            <Text style={styles.subtitle}>Enter the 6-digit code sent by {channel} to {activeIdentifier}.</Text>
            {devHintCode ? (
              <View style={styles.devHintBox}>
                <Text style={styles.devHintLabel}>SYSTEM OTP CODE</Text>
                <Text style={styles.devHintValue}>{devHintCode}</Text>
              </View>
            ) : null}
            <Text style={styles.label}>VERIFICATION CODE</Text>
            <TextInput style={[styles.input, styles.code]} value={code} onChangeText={setCode} keyboardType="number-pad" maxLength={6} placeholder="• • • • • •" placeholderTextColor="#64748B" />
            <TouchableOpacity style={styles.button} onPress={verify} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>VERIFY & CONTINUE</Text>}
            </TouchableOpacity>
            <TouchableOpacity onPress={resend} disabled={resendSeconds > 0 || loading} style={styles.secondary}>
              <Text style={styles.secondaryText}>{resendSeconds > 0 ? `Resend code in ${resendSeconds}s` : 'Resend verification code'}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setStep('credentials')} style={styles.secondary}>
              <Text style={styles.muted}>← Change verification method</Text>
            </TouchableOpacity>
          </>}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: {flex: 1, backgroundColor: '#05070D'},
  content: {flexGrow: 1, justifyContent: 'center', padding: 22},
  brand: {color: '#fff', textAlign: 'center', fontSize: 28, fontWeight: '900', letterSpacing: 3},
  tagline: {color: '#7083FF', textAlign: 'center', fontSize: 9, fontWeight: '800', letterSpacing: 2, marginTop: 5, marginBottom: 20},
  card: {backgroundColor: '#0A0E18', borderWidth: 1, borderColor: '#1E293B', borderRadius: 20, padding: 20},
  tabs: {flexDirection: 'row', backgroundColor: '#05070D', borderRadius: 12, padding: 4, marginBottom: 22},
  tab: {flex: 1, padding: 11, alignItems: 'center', borderRadius: 9},
  activeTab: {backgroundColor: '#1E293B'},
  tabText: {color: '#E2E8F0', fontWeight: '800'},
  title: {color: '#fff', fontSize: 23, fontWeight: '900', marginBottom: 7},
  subtitle: {color: '#7D8AA8', fontSize: 12.5, lineHeight: 19, marginBottom: 20},
  label: {color: '#8995B1', fontSize: 9.5, fontWeight: '800', letterSpacing: 1.1, marginBottom: 8, marginTop: 3},
  input: {height: 50, borderRadius: 12, borderWidth: 1, borderColor: '#1E293B', backgroundColor: '#05070D', color: '#fff', paddingHorizontal: 14, marginBottom: 15},
  channels: {flexDirection: 'row', gap: 7, marginBottom: 20},
  channel: {flex: 1, minHeight: 70, borderWidth: 1, borderColor: '#1E293B', backgroundColor: '#05070D', borderRadius: 12, alignItems: 'center', justifyContent: 'center'},
  channelActive: {borderColor: '#7083FF', backgroundColor: '#7083FF18'},
  channelIcon: {color: '#fff', fontSize: 19, marginBottom: 5},
  channelText: {color: '#CBD5E1', fontSize: 10.5, fontWeight: '800'},
  button: {height: 52, borderRadius: 12, backgroundColor: '#334BFF', alignItems: 'center', justifyContent: 'center'},
  buttonText: {color: '#fff', fontSize: 11, fontWeight: '900', letterSpacing: 1},
  code: {fontSize: 24, fontWeight: '900', textAlign: 'center', letterSpacing: 8},
  devHintBox: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#334BFF18', borderWidth: 1, borderColor: '#334BFF40', borderRadius: 10, paddingHorizontal: 14, paddingVertical: 10, marginBottom: 16},
  devHintLabel: {color: '#7083FF', fontSize: 10, fontWeight: '800', letterSpacing: 1},
  devHintValue: {color: '#35E68A', fontSize: 20, fontWeight: '900', letterSpacing: 3},
  secondary: {alignItems: 'center', marginTop: 17},
  secondaryText: {color: '#7083FF', fontWeight: '800', fontSize: 12},
  muted: {color: '#64748B', fontWeight: '700', fontSize: 11.5},
});
