# 🧪 Testing RepEnhance iOS App on Desktop

## 📱 Option 1: iOS Simulator (Recommended)

### Prerequisites Check
1. **Xcode**: Make sure Xcode is installed from the App Store
2. **iOS Simulator**: Comes with Xcode
3. **React Native CLI**: Already installed

### Step-by-Step Testing:

#### 1. Start the Backend Server First
```bash
# Navigate to the original web app backend
cd "innate apps/repenhance-fullstack"

# Start the backend API server
npm run server
# This should start on http://localhost:3001
```

#### 2. Open iOS Simulator
```bash
# Open iOS Simulator directly
open -a Simulator

# Or let React Native open it automatically (next step)
```

#### 3. Start the React Native App
```bash
# Navigate to the iOS app
cd "innate apps/RepEnhanceApp"

# Start Metro bundler
npx react-native start

# In another terminal, run the iOS app
npx react-native run-ios
```

### 🎯 What Should Happen:
1. iOS Simulator opens with iPhone interface
2. RepEnhance app launches automatically
3. You see the dark-themed input screen
4. You can fill out the form and test the full flow

---

## 📱 Option 2: Expo Go (Alternative)

If React Native CLI has issues, we can convert to Expo:

#### 1. Install Expo CLI
```bash
npm install -g @expo/cli
```

#### 2. Initialize Expo Project
```bash
cd "innate apps"
npx create-expo-app RepEnhanceExpo --template blank
# Then copy our src files over
```

#### 3. Run with Expo
```bash
cd RepEnhanceExpo
npx expo start
# Press 'i' for iOS simulator
```

---

## 🔧 Troubleshooting Common Issues

### Issue 1: "No iOS devices connected"
**Solution:**
```bash
# List available simulators
xcrun simctl list devices

# Boot a specific simulator
xcrun simctl boot "iPhone 15"

# Then try running the app again
npx react-native run-ios
```

### Issue 2: "Metro bundler not starting"
**Solution:**
```bash
# Clear Metro cache
npx react-native start --reset-cache

# Or manually clear
rm -rf node_modules
npm install
```

### Issue 3: "Build failed"
**Solution:**
```bash
# Clean build
cd ios
xcodebuild clean
cd ..
npx react-native run-ios
```

### Issue 4: "API connection failed"
**Solution:**
- Make sure backend is running on localhost:3001
- Check that both apps are running simultaneously
- Verify API endpoints in src/services/api.js

---

## 🎮 Testing Checklist

### ✅ Input Screen Testing:
- [ ] App launches with dark theme
- [ ] Form fields accept input
- [ ] Validation works (try submitting without name/location)
- [ ] Button states change correctly
- [ ] Keyboard handling works properly

### ✅ Loading Screen Testing:
- [ ] Smooth transition from input
- [ ] Progress indicators animate
- [ ] Steps complete in sequence
- [ ] API call is made to backend

### ✅ Results Screen Testing:
- [ ] Reputation scores display correctly
- [ ] Recommendation cards are interactive
- [ ] "Get guide" buttons work
- [ ] Pull-to-refresh functions
- [ ] Navigation back to input works

### ✅ API Integration Testing:
- [ ] Backend receives requests
- [ ] Data flows correctly between screens
- [ ] Error handling works for network issues
- [ ] Loading states display properly

---

## 🚀 Quick Start Commands

```bash
# Terminal 1: Start Backend
cd "innate apps/repenhance-fullstack" && npm run server

# Terminal 2: Start iOS App
cd "innate apps/RepEnhanceApp" && npx react-native run-ios
```

## 📱 Expected User Flow:
1. **Input Screen**: Enter name, location, affiliation
2. **Loading Screen**: Watch progress indicators (3-5 seconds)
3. **Results Screen**: View reputation scores and recommendations
4. **Interaction**: Tap "Get guide" buttons to expand details
5. **Navigation**: Use "← New Scan" to return to input

The app should feel smooth and responsive, just like a native iOS app!
