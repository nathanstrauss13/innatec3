# RepRead - AI Reputation Management App

## 🚀 Complete React Native iOS App

RepRead is a professional AI reputation management app that analyzes how ChatGPT, Claude, Gemini, and Perplexity represent you when people search for your name. Get actionable insights to enhance your digital presence.

## ✨ Features

### **Core Features:**
- **Professional Input Form** - Name, location, company, job title
- **Real-time Analysis** - Live visualization of 52+ AI queries
- **Freemium Model** - Basic scan + premium paywall ($4.99 single / $19.99 Pro)
- **Comprehensive Results** - Tabbed interface with Overview, AI Knowledge, Discrepancies, Action Plan
- **Word Cloud Visualization** - See what words AI associates with you
- **Actionable Recommendations** - Ranked by impact and effort
- **Social Sharing** - Share your AI reputation score

### **Advanced Features:**
- **Multi-AI Analysis** - ChatGPT-4, Claude, Gemini, Perplexity
- **Real-time Progress Tracking** - Live query execution visualization
- **Professional Scoring** - Overall, Professional, Visibility, Accuracy metrics
- **Discrepancy Detection** - Identify inconsistencies across AI platforms
- **Analytics Integration** - User journey and conversion tracking
- **Dark Theme UI** - Professional, mobile-optimized design

## 🛠 Setup Instructions

### **Prerequisites:**
- Node.js 18+ installed
- Expo CLI installed globally: `npm install -g @expo/cli`
- iOS Simulator (for iOS testing) or Android Studio (for Android)

### **Installation:**

1. **Navigate to the app directory:**
   ```bash
   cd "innate apps/RepReadApp"
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

4. **Run on iOS Simulator:**
   ```bash
   npm run ios
   ```

5. **Run on Android:**
   ```bash
   npm run android
   ```

## 📱 App Structure

```
RepReadApp/
├── App.js                 # Main app component with navigation
├── package.json           # Dependencies and scripts
├── app.json              # Expo configuration
├── README.md             # This file
└── assets/               # App icons and splash screens
```

## 🎯 Key Components

### **InputScreen**
- Professional form with name, location, company, title
- Real-time validation and focus states
- Privacy notice and secure data messaging

### **LoadingScreen**
- Real-time query visualization across 4 AI platforms
- Live progress tracking with 52+ queries
- Category breakdown (Identity, Professional, Location, Recent Activity)

### **PaywallScreen**
- Freemium model with basic results preview
- Two pricing options: $4.99 single analysis / $19.99 Pro subscription
- Clear value proposition and upgrade incentives

### **ResultsScreen**
- Tabbed interface: Overview, AI Knowledge, Discrepancies, Action Plan
- Professional scoring with color-coded metrics
- Word cloud visualization (Pro feature)
- Actionable recommendations with impact/effort ratings
- Social sharing capabilities

## 🔧 Configuration

### **API Integration:**
The app includes a mock API service for development. To connect to a real backend:

1. Update the `APIService` class in `App.js`
2. Replace the `baseURL` with your production API endpoint
3. Implement real AI API calls (OpenAI, Anthropic, Google, Perplexity)

### **Analytics:**
The app includes analytics tracking hooks. To enable:

1. Install Firebase Analytics: `expo install @react-native-firebase/analytics`
2. Update the `AnalyticsService` class with real tracking calls
3. Configure Firebase project and add configuration files

### **Payment Processing:**
To enable real payments:

1. Install Stripe or Apple Pay SDK
2. Update the `handlePurchase` function in `PaywallScreen`
3. Implement server-side payment processing

## 🎨 Design System

### **Colors:**
- **Primary**: Blue (#3b82f6, #60a5fa, #2563eb)
- **Success**: Green (#4ade80, #22c55e)
- **Warning**: Yellow (#facc15)
- **Error**: Red (#f87171)
- **Gray Scale**: 9 shades from #111827 to #e5e7eb

### **Typography:**
- **Titles**: 30px, bold
- **Subtitles**: 20px, medium
- **Body**: 16px, regular
- **Labels**: 14px, medium
- **Captions**: 12px, regular

## 📊 Analytics Events

The app tracks the following events:
- `screen_view` - Screen navigation
- `analysis_start` - User begins analysis
- `analysis_complete` - Analysis finished
- `paywall_view` - Paywall displayed
- `purchase` - Successful purchase
- `share` - Content shared

## 🚀 Deployment

### **iOS App Store:**
1. Build for production: `expo build:ios`
2. Upload to App Store Connect
3. Submit for review

### **Android Play Store:**
1. Build for production: `expo build:android`
2. Upload to Google Play Console
3. Submit for review

## 🔐 Security & Privacy

- **Data Encryption**: All API calls use HTTPS
- **No Persistent Storage**: User data is not stored permanently
- **Privacy Notice**: Clear messaging about data usage
- **Secure Payment**: Industry-standard payment processing

## 📈 Performance

- **Optimized Rendering**: Efficient React Native components
- **Lazy Loading**: Components loaded as needed
- **Caching**: API responses cached for better performance
- **Error Handling**: Comprehensive error boundaries

## 🎯 Next Steps

1. **Add Real API Integration** - Connect to actual AI APIs
2. **Implement Payment Processing** - Stripe/Apple Pay integration
3. **Add Firebase Analytics** - Real user tracking
4. **Push Notifications** - Pro user alerts
5. **Offline Support** - Cache results for offline viewing
6. **A/B Testing** - Optimize conversion rates

## 📝 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For technical support or questions, contact the development team.

---

**RepRead** - See what AI knows about you. Enhance your professional reputation.
