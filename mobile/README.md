# Saraphina Mobile App

React Native mobile application for iOS and Android with background location tracking, push notifications, and offline-first architecture.

## Features

- 📍 Background location tracking
- 🔔 Push notifications (FCM/APNS)
- 📱 Offline-first with local SQLite storage
- 🔄 Auto-sync when network available
- 🗺️ Interactive maps with device tracking
- 🔐 Biometric authentication
- 🌙 Dark mode support

## Setup

```bash
npm install
# or
yarn install

# iOS
cd ios && pod install && cd ..

# Run
npm run ios
npm run android
```

## Architecture

```
mobile/
├── src/
│   ├── components/       # Reusable UI components
│   ├── screens/          # App screens
│   ├── services/         # API and background services
│   ├── store/            # Redux store
│   ├── utils/            # Utilities
│   └── App.tsx
├── android/              # Android native code
├── ios/                  # iOS native code
└── package.json
```

## Background Location Tracking

Uses `react-native-background-geolocation` with configurable update intervals and geofencing support.

```typescript
// Example configuration
BackgroundGeolocation.ready({
  desiredAccuracy: BackgroundGeolocation.DESIRED_ACCURACY_HIGH,
  distanceFilter: 10,
  stopTimeout: 5,
  debug: false,
  logLevel: BackgroundGeolocation.LOG_LEVEL_VERBOSE,
  stopOnTerminate: false,
  startOnBoot: true,
  url: 'https://api.saraphina.local/telemetry',
  autoSync: true,
});
```

## Push Notifications

Integrated with Firebase Cloud Messaging (FCM) and Apple Push Notification Service (APNS).

## Offline Sync

Uses SQLite for local storage with automatic conflict resolution when syncing with server.

## Build & Deploy

```bash
# iOS
npm run build:ios

# Android
npm run build:android

# Generate release APK
cd android && ./gradlew assembleRelease
```

## Environment Variables

Create `.env` file:

```
API_BASE_URL=https://api.saraphina.local
MAPBOX_TOKEN=your_mapbox_token
FIREBASE_API_KEY=your_firebase_key
```
