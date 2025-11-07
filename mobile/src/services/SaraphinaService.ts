/**
 * Saraphina Mobile Service
 * Handles API communication, offline sync, and background tasks
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import BackgroundGeolocation from 'react-native-background-geolocation';
import messaging from '@react-native-firebase/messaging';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

interface Device {
  device_id: string;
  name: string;
  last_location?: [number, number];
  battery_level?: number;
}

interface TelemetryData {
  device_id: string;
  location: [number, number];
  accuracy: number;
  battery_level: number;
  timestamp: number;
}

class SaraphinaService {
  private authToken: string | null = null;
  private syncQueue: TelemetryData[] = [];
  private isOnline: boolean = true;

  constructor() {
    this.init();
  }

  private async init() {
    // Monitor network connectivity
    NetInfo.addEventListener(state => {
      this.isOnline = state.isConnected || false;
      if (this.isOnline) {
        this.syncOfflineData();
      }
    });

    // Setup background location tracking
    this.setupBackgroundTracking();

    // Setup push notifications
    this.setupPushNotifications();

    // Load auth token
    this.authToken = await AsyncStorage.getItem('auth_token');
  }

  // ============ Authentication ============

  async login(username: string, password: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        this.authToken = data.token;
        await AsyncStorage.setItem('auth_token', data.token);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  }

  async logout() {
    this.authToken = null;
    await AsyncStorage.removeItem('auth_token');
    BackgroundGeolocation.stop();
  }

  // ============ Device Management ============

  async getDevices(): Promise<Device[]> {
    try {
      const response = await this.authenticatedFetch('/api/devices');
      if (response.ok) {
        return await response.json();
      }
      
      // Fallback to cached devices if offline
      const cached = await AsyncStorage.getItem('cached_devices');
      return cached ? JSON.parse(cached) : [];
    } catch (error) {
      console.error('Get devices error:', error);
      return [];
    }
  }

  async trackDevice(deviceId: string): Promise<any> {
    const response = await this.authenticatedFetch(`/api/track/${deviceId}`);
    return response.json();
  }

  async startRecovery(deviceId: string): Promise<string> {
    const response = await this.authenticatedFetch(`/api/recover/${deviceId}`, {
      method: 'POST',
    });
    const data = await response.json();
    return data.session_id;
  }

  // ============ Background Location Tracking ============

  private async setupBackgroundTracking() {
    BackgroundGeolocation.ready({
      desiredAccuracy: BackgroundGeolocation.DESIRED_ACCURACY_HIGH,
      distanceFilter: 10,
      stopTimeout: 5,
      debug: false,
      logLevel: BackgroundGeolocation.LOG_LEVEL_VERBOSE,
      stopOnTerminate: false,
      startOnBoot: true,
      notification: {
        title: 'Saraphina Location Tracking',
        text: 'Tracking your device location',
      },
    }).then(() => {
      BackgroundGeolocation.on('location', this.handleLocationUpdate.bind(this));
      BackgroundGeolocation.start();
    });
  }

  private async handleLocationUpdate(location: any) {
    const telemetry: TelemetryData = {
      device_id: await this.getDeviceId(),
      location: [location.coords.latitude, location.coords.longitude],
      accuracy: location.coords.accuracy,
      battery_level: location.battery.level * 100,
      timestamp: Date.now(),
    };

    if (this.isOnline) {
      await this.sendTelemetry(telemetry);
    } else {
      // Queue for later sync
      this.syncQueue.push(telemetry);
      await this.saveSyncQueue();
    }
  }

  private async sendTelemetry(telemetry: TelemetryData) {
    try {
      await this.authenticatedFetch('/api/telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(telemetry),
      });
    } catch (error) {
      console.error('Telemetry error:', error);
      this.syncQueue.push(telemetry);
    }
  }

  // ============ Offline Sync ============

  private async syncOfflineData() {
    if (this.syncQueue.length === 0) return;

    console.log(`Syncing ${this.syncQueue.length} offline telemetry records...`);

    const batch = [...this.syncQueue];
    this.syncQueue = [];

    try {
      await this.authenticatedFetch('/api/telemetry/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ telemetry: batch }),
      });

      console.log('Sync complete');
      await AsyncStorage.removeItem('sync_queue');
    } catch (error) {
      console.error('Sync error:', error);
      // Re-queue failed items
      this.syncQueue = [...batch, ...this.syncQueue];
    }
  }

  private async saveSyncQueue() {
    await AsyncStorage.setItem('sync_queue', JSON.stringify(this.syncQueue));
  }

  private async loadSyncQueue() {
    const queue = await AsyncStorage.getItem('sync_queue');
    if (queue) {
      this.syncQueue = JSON.parse(queue);
    }
  }

  // ============ Push Notifications ============

  private async setupPushNotifications() {
    // Request permission
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      // Get FCM token
      const token = await messaging().getToken();
      await this.registerPushToken(token);

      // Handle foreground messages
      messaging().onMessage(async remoteMessage => {
        console.log('Push notification:', remoteMessage);
        // Show local notification or update UI
      });

      // Handle background/quit messages
      messaging().setBackgroundMessageHandler(async remoteMessage => {
        console.log('Background notification:', remoteMessage);
      });
    }
  }

  private async registerPushToken(token: string) {
    try {
      await this.authenticatedFetch('/api/push/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, platform: 'android' }), // or 'ios'
      });
    } catch (error) {
      console.error('Push token registration error:', error);
    }
  }

  // ============ Utilities ============

  private async authenticatedFetch(endpoint: string, options: RequestInit = {}) {
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.authToken}`,
    };

    return fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  }

  private async getDeviceId(): Promise<string> {
    let deviceId = await AsyncStorage.getItem('device_id');
    if (!deviceId) {
      deviceId = `device-${Math.random().toString(36).substr(2, 9)}`;
      await AsyncStorage.setItem('device_id', deviceId);
    }
    return deviceId;
  }
}

export default new SaraphinaService();
