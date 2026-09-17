import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthenticatedUser } from '../navigation/navigationTypes';

const LEGACY_PHOTO_KEY = '@bally_profile_photo';

/**
 * Builds a sanitized, user-specific key for storing and retrieving profile pictures.
 * This guarantees that when different users log in on the same device,
 * their profile photos remain strictly isolated.
 */
export function getScopedPhotoKey(userIdentifier?: string | null): string {
  if (!userIdentifier || !userIdentifier.trim()) {
    return LEGACY_PHOTO_KEY;
  }
  const cleanId = userIdentifier.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  return `@bally_profile_photo_${cleanId}`;
}

/**
 * Resolves the identifier (id or email) of the currently authenticated user.
 */
export async function resolveCurrentUserIdentifier(
  userParam?: AuthenticatedUser | null,
): Promise<string | null> {
  if (userParam?.id && String(userParam.id).trim().length > 0) {
    return String(userParam.id).trim().toLowerCase();
  }
  if (userParam?.email && userParam.email.trim().length > 0) {
    return userParam.email.trim().toLowerCase();
  }

  try {
    const raw = await AsyncStorage.getItem('@bally_auth_user');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed?.id && String(parsed.id).trim().length > 0) {
        return String(parsed.id).trim().toLowerCase();
      }
      if (parsed?.email && String(parsed.email).trim().length > 0) {
        return String(parsed.email).trim().toLowerCase();
      }
    }
  } catch {
    // Ignore parse errors
  }

  return null;
}

/**
 * Loads the profile photo URI for the current user. Returns null if none is saved.
 */
export async function loadUserProfilePhoto(
  userParam?: AuthenticatedUser | null,
): Promise<string | null> {
  try {
    const identifier = await resolveCurrentUserIdentifier(userParam);
    if (!identifier) {
      return null;
    }
    const scopedKey = getScopedPhotoKey(identifier);
    const photo = await AsyncStorage.getItem(scopedKey);
    return photo || null;
  } catch {
    return null;
  }
}

/**
 * Persists the profile photo URI for the current user under their scoped key.
 */
export async function saveUserProfilePhoto(
  uri: string,
  userParam?: AuthenticatedUser | null,
): Promise<void> {
  try {
    const identifier = await resolveCurrentUserIdentifier(userParam);
    if (!identifier) {
      return;
    }
    const scopedKey = getScopedPhotoKey(identifier);
    await AsyncStorage.setItem(scopedKey, uri);
  } catch {
    // Ignore storage errors
  }
}

/**
 * Clears the profile photo URI for the current user upon logout or profile reset.
 */
export async function clearUserProfilePhoto(
  userParam?: AuthenticatedUser | null,
): Promise<void> {
  try {
    const identifier = await resolveCurrentUserIdentifier(userParam);
    if (identifier) {
      const scopedKey = getScopedPhotoKey(identifier);
      await AsyncStorage.removeItem(scopedKey);
    }
    await AsyncStorage.removeItem(LEGACY_PHOTO_KEY);
  } catch {
    // Ignore storage errors
  }
}
