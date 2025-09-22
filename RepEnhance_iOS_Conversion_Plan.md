# RepEnhance iOS App Conversion Plan

## Current Web App Analysis
- **Framework**: React 18.2.0 with Create React App
- **Styling**: Tailwind CSS (via CDN)
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Backend**: Node.js/Express API (unchanged)

## React Native Dependencies Mapping

### Core Dependencies
- `react` → Keep same version (18.2.0)
- `react-dom` → Remove (web-only)
- `react-scripts` → Remove (web-only)
- `axios` → Keep for API calls
- `lucide-react` → Replace with `react-native-vector-icons`

### New React Native Dependencies Needed
```json
{
  "@react-navigation/native": "^6.1.9",
  "@react-navigation/stack": "^6.3.20",
  "react-native-vector-icons": "^10.0.3",
  "react-native-safe-area-context": "^4.7.4",
  "react-native-screens": "^3.27.0",
  "react-native-gesture-handler": "^2.14.0"
}
```

## Component Conversion Strategy

### 1. App.js Main Component
**Current Structure**:
- Input form screen
- Loading/scanning screen  
- Results screen with multiple sections

**React Native Conversion**:
- Convert to Stack Navigator with 3 screens
- Replace `div` → `View`
- Replace `input` → `TextInput`
- Replace `button` → `TouchableOpacity` or `Pressable`

### 2. Styling Conversion
**Current**: Tailwind CSS classes
**Target**: React Native StyleSheet

**Key Conversions**:
- `className="bg-gray-900"` → `style={styles.backgroundDark}`
- `className="text-white"` → `style={styles.textWhite}`
- `className="flex items-center"` → `style={styles.flexCenter}`

### 3. Icon Conversion
**Current**: Lucide React icons
**Target**: React Native Vector Icons

**Example**:
```jsx
// Before
<Search className="w-5 h-5 mr-2" />

// After  
<Icon name="search" size={20} color="#60A5FA" style={styles.iconMargin} />
```

## Screen Structure

### Screen 1: Input Form
- Name input field
- Location input field  
- Affiliation input field
- Submit button
- Feature highlights section

### Screen 2: Analysis Loading
- Animated loading spinner
- Progress indicators
- Status messages

### Screen 3: Results Dashboard
- Reputation scores (4 metrics)
- AI search patterns
- Findings summary
- Recommendations list
- Action guides (expandable)

## API Integration
- Keep existing backend API unchanged
- Update base URL for mobile (localhost won't work on device)
- Add proper error handling for mobile network conditions
- Implement retry logic for failed requests

## iOS-Specific Features to Add
1. **Navigation**: Native iOS navigation patterns
2. **Haptic Feedback**: For button presses and interactions
3. **Pull to Refresh**: On results screen
4. **Share Functionality**: Share reports via iOS share sheet
5. **Dark Mode**: Respect iOS system dark mode setting
6. **Safe Areas**: Handle iPhone notch and home indicator
7. **Keyboard Handling**: Proper keyboard avoidance

## Development Phases

### Phase 1: Basic Structure (Days 1-3)
- Set up React Native project
- Create navigation structure
- Convert input form screen
- Basic styling implementation

### Phase 2: Core Functionality (Days 4-6)
- Implement API integration
- Convert loading screen with animations
- Build results screen layout
- Add basic error handling

### Phase 3: Polish & iOS Features (Days 7-10)
- Implement native iOS patterns
- Add haptic feedback and animations
- Optimize for different screen sizes
- Add app icons and splash screen
- Test on physical device

### Phase 4: App Store Preparation (Days 11-14)
- Code signing setup
- App Store metadata
- Screenshots and descriptions
- Final testing and optimization

## File Structure for React Native App
```
RepEnhanceApp/
├── src/
│   ├── screens/
│   │   ├── InputScreen.js
│   │   ├── LoadingScreen.js
│   │   └── ResultsScreen.js
│   ├── components/
│   │   ├── ReputationScore.js
│   │   ├── SearchQuery.js
│   │   └── ActionItem.js
│   ├── services/
│   │   └── api.js
│   ├── styles/
│   │   └── styles.js
│   └── navigation/
│       └── AppNavigator.js
├── ios/
└── android/
```

## Next Steps
1. Wait for React Native CLI installation to complete
2. Create project structure
3. Install additional dependencies
4. Begin component conversion
5. Set up iOS development environment
