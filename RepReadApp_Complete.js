// Complete RepRead React Native Implementation
// This file contains all enhanced components for the RepRead app

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Modal,
  Dimensions,
  Share,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import axios from 'axios';

// ============================================================================
// STYLES & CONSTANTS
// ============================================================================

const { width, height } = Dimensions.get('window');

const colors = {
  gray900: '#111827',
  gray800: '#1f2937',
  gray700: '#374151',
  gray600: '#4b5563',
  gray500: '#6b7280',
  gray400: '#9ca3af',
  gray300: '#d1d5db',
  gray200: '#e5e7eb',
  blue500: '#3b82f6',
  blue400: '#60a5fa',
  blue600: '#2563eb',
  green400: '#4ade80',
  green500: '#22c55e',
  yellow400: '#facc15',
  red400: '#f87171',
  white: '#ffffff',
  black: '#000000',
};

const styles = {
  // Base styles
  container: {
    flex: 1,
    backgroundColor: colors.gray900,
  },
  safeArea: {
    flex: 1,
    backgroundColor: colors.gray900,
  },
  scrollContainer: {
    flexGrow: 1,
    paddingHorizontal: 16,
    paddingVertical: 24,
  },
  
  // Card styles
  card: {
    backgroundColor: colors.gray800,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.gray700,
    padding: 32,
    marginBottom: 24,
  },
  
  // Text styles
  title: {
    fontSize: 30,
    fontWeight: 'bold',
    color: colors.white,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 20,
    fontWeight: '500',
    color: colors.gray300,
    textAlign: 'center',
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    color: colors.gray400,
    textAlign: 'center',
    lineHeight: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.white,
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.gray200,
    marginBottom: 8,
  },
  
  // Input styles
  input: {
    backgroundColor: colors.gray700,
    borderWidth: 1,
    borderColor: colors.gray600,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 16,
    fontSize: 16,
    color: colors.white,
    marginBottom: 16,
  },
  inputFocused: {
    borderColor: colors.blue500,
    borderWidth: 2,
  },
  
  // Button styles
  primaryButton: {
    backgroundColor: colors.blue600,
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonDisabled: {
    backgroundColor: colors.gray600,
    opacity: 0.5,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.white,
  },
  
  // Loading styles
  loadingContainer: {
    flex: 1,
    backgroundColor: colors.gray900,
    padding: 16,
  },
  progressHeader: {
    alignItems: 'center',
    marginBottom: 32,
  },
  loadingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.white,
    marginBottom: 8,
  },
  progressCounter: {
    fontSize: 16,
    color: colors.gray400,
    marginBottom: 16,
  },
  overallProgressBar: {
    width: '100%',
    height: 8,
    backgroundColor: colors.gray700,
    borderRadius: 4,
  },
  overallProgressFill: {
    height: '100%',
    backgroundColor: colors.blue500,
    borderRadius: 4,
  },
  
  // Query visualization styles
  liveQueryFeed: {
    marginBottom: 24,
  },
  queryServiceCard: {
    backgroundColor: colors.gray800,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.gray700,
  },
  queryServiceCardActive: {
    borderColor: colors.blue500,
    backgroundColor: colors.gray700,
  },
  serviceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  serviceIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  serviceInfo: {
    flex: 1,
  },
  serviceName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.white,
  },
  serviceProgress: {
    fontSize: 14,
    color: colors.gray400,
  },
  currentQuery: {
    backgroundColor: colors.gray700,
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  currentQueryText: {
    fontSize: 14,
    color: colors.blue400,
    fontStyle: 'italic',
  },
  serviceProgressBar: {
    height: 4,
    backgroundColor: colors.gray700,
    borderRadius: 2,
  },
  serviceProgressFill: {
    height: '100%',
    borderRadius: 2,
  },
  
  // Word cloud styles
  wordCloudContainer: {
    marginBottom: 24,
  },
  wordCloudSubtitle: {
    fontSize: 14,
    color: colors.gray400,
    textAlign: 'center',
    marginBottom: 24,
  },
  wordCloudCanvas: {
    height: 400,
    backgroundColor: colors.gray800,
    borderRadius: 12,
    position: 'relative',
    marginBottom: 16,
  },
  wordItem: {
    padding: 4,
  },
  wordText: {
    color: colors.white,
  },
  wordCloudLegend: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flexWrap: 'wrap',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  legendLabel: {
    fontSize: 12,
    color: colors.gray400,
  },
  
  // Tab styles
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: colors.gray800,
    borderRadius: 12,
    margin: 16,
    padding: 4,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: colors.blue600,
  },
  tabTitle: {
    fontSize: 14,
    color: colors.gray400,
    marginLeft: 4,
  },
  activeTabTitle: {
    color: colors.white,
  },
  
  // Score styles
  scoreContainer: {
    alignItems: 'center',
    padding: 16,
  },
  scoreValue: {
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  scoreLabel: {
    fontSize: 12,
    color: colors.gray400,
    textTransform: 'uppercase',
  },
  scoreHigh: {
    color: colors.green400,
  },
  scoreMedium: {
    color: colors.yellow400,
  },
  scoreLow: {
    color: colors.red400,
  },
  
  // Grid styles
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
  },
  gridItem: {
    flex: 1,
    marginHorizontal: 8,
    minWidth: width / 2 - 24,
  },
  
  // Paywall styles
  paywallContainer: {
    flex: 1,
    backgroundColor: colors.gray900,
    padding: 16,
    justifyContent: 'center',
  },
  paywallTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.white,
    textAlign: 'center',
    marginBottom: 16,
  },
  paywallDescription: {
    fontSize: 16,
    color: colors.gray400,
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  pricingContainer: {
    marginBottom: 32,
  },
  pricingOption: {
    backgroundColor: colors.gray800,
    borderRadius: 16,
    padding: 24,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: colors.gray700,
  },
  pricingOptionSelected: {
    borderColor: colors.blue500,
  },
  pricingTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.white,
    marginBottom: 8,
  },
  pricingPrice: {
    fontSize: 32,
    fontWeight: 'bold',
    color: colors.blue400,
    marginBottom: 8,
  },
  pricingDescription: {
    fontSize: 14,
    color: colors.gray400,
    lineHeight: 20,
  },
  
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  wordDetailModal: {
    backgroundColor: colors.gray800,
    borderRadius: 16,
    padding: 24,
    margin: 20,
    maxHeight: height * 0.7,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.white,
  },
};

// ============================================================================
// API SERVICE
// ============================================================================

class APIService {
  constructor() {
    this.baseURL = __DEV__ 
      ? 'http://localhost:3002/api' 
      : 'https://your-production-api.com/api';
  }

  async analyzeReputation(formData) {
    // Mock comprehensive analysis for development
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return {
      timestamp: new Date().toISOString(),
      person: formData,
      queryStats: {
        totalQueries: 52,
        completedQueries: 52,
        aiPlatforms: 4
      },
      scores: {
        overall: Math.floor(Math.random() * 30) + 65,
        professional: Math.floor(Math.random() * 25) + 70,
        visibility: Math.floor(Math.random() * 40) + 45,
        accuracy: Math.floor(Math.random() * 20) + 75,
        consistency: Math.floor(Math.random() * 20) + 80
      },
      platformsFound: Math.floor(Math.random() * 2) + 3, // 3-4 platforms
      aiResponses: {
        gpt4: this.generateMockResponses(formData, 15),
        claude: this.generateMockResponses(formData, 15),
        gemini: this.generateMockResponses(formData, 12),
        perplexity: this.generateMockResponses(formData, 10)
      },
      wordCloud: this.generateWordCloudData(formData),
      discrepancies: this.generateDiscrepancies(formData),
      recommendations: this.generateRecommendations()
    };
  }

  generateMockResponses(formData, count) {
    const responses = [];
    const baseResponses = [
      `${formData.name} is a professional based in ${formData.location}.`,
      `I found information about ${formData.name}, including their work at ${formData.company || 'their current company'}.`,
      `${formData.name} appears to be known for their expertise in their field.`,
      `Based on available information, ${formData.name} has a strong professional presence.`,
      `${formData.name} is associated with ${formData.company || 'professional work'} in ${formData.location}.`
    ];
    
    for (let i = 0; i < count; i++) {
      responses.push({
        query: `Query ${i + 1} about ${formData.name}`,
        response: baseResponses[i % baseResponses.length],
        confidence: Math.random() > 0.3 ? 'high' : 'medium'
      });
    }
    
    return responses;
  }

  generateWordCloudData(formData) {
    const baseWords = [
      { word: formData.name.split(' ')[0], count: 48, sources: ['gpt4', 'claude', 'gemini', 'perplexity'] },
      { word: formData.name.split(' ')[1] || 'Professional', count: 47, sources: ['gpt4', 'claude', 'gemini', 'perplexity'] },
      { word: 'professional', count: 32, sources: ['gpt4', 'claude', 'gemini'] },
      { word: 'expert', count: 28, sources: ['gpt4', 'claude'] },
      { word: 'leadership', count: 24, sources: ['claude', 'gemini', 'perplexity'] },
      { word: 'experienced', count: 22, sources: ['gpt4', 'gemini'] },
      { word: 'innovative', count: 18, sources: ['claude', 'perplexity'] },
      { word: 'strategic', count: 16, sources: ['gpt4'] },
      { word: 'accomplished', count: 14, sources: ['claude', 'gemini'] },
      { word: 'respected', count: 12, sources: ['perplexity'] }
    ];

    if (formData.company) {
      baseWords.splice(2, 0, {
        word: formData.company,
        count: 35,
        sources: ['gpt4', 'claude', 'gemini']
      });
    }

    if (formData.location) {
      baseWords.splice(4, 0, {
        word: formData.location.split(',')[0],
        count: 20,
        sources: ['gpt4', 'gemini']
      });
    }

    return baseWords.map((item, index) => ({
      ...item,
      size: Math.min(Math.max(item.count * 0.8 + 12, 14), 32),
      color: this.getWordColor(item.sources.length),
      x: Math.random() * (width - 160) + 40,
      y: Math.random() * 300 + 50
    }));
  }

  getWordColor(sourceCount) {
    if (sourceCount === 4) return colors.green400;
    if (sourceCount === 3) return colors.blue400;
    if (sourceCount === 2) return colors.yellow400;
    return colors.gray400;
  }

  generateDiscrepancies(formData) {
    const discrepancies = [];
    
    if (Math.random() > 0.5) {
      discrepancies.push({
        type: 'job_title',
        severity: 'medium',
        title: 'Job Title Variations',
        description: 'AI platforms show slightly different versions of your job title',
        details: [
          { platform: 'ChatGPT', content: `${formData.title || 'Senior Director'}`, icon: '🤖', color: colors.green400 },
          { platform: 'Claude', content: `${formData.title || 'Director'}`, icon: '🧠', color: colors.yellow400 },
        ],
        impact: 'May cause confusion about your current role level',
        recommendation: 'Update your LinkedIn headline to match your preferred title'
      });
    }

    return discrepancies;
  }

  generateRecommendations() {
    return [
      {
        title: 'Optimize LinkedIn Profile',
        description: 'Update your headline and summary to improve AI discoverability',
        impact: 'high',
        effort: 'low',
        category: 'professional_presence',
        automated: false,
        actionType: 'linkedin_optimization'
      },
      {
        title: 'Create Thought Leadership Content',
        description: 'Publish articles to establish expertise and improve AI knowledge',
        impact: 'high',
        effort: 'medium',
        category: 'content_creation',
        automated: false,
        actionType: 'content_strategy'
      },
      {
        title: 'Update Company Website Bio',
        description: 'Ensure your company bio reflects current role and achievements',
        impact: 'medium',
        effort: 'low',
        category: 'source_optimization',
        automated: true,
        actionType: 'bio_optimization'
      }
    ];
  }
}

// ============================================================================
// ANALYTICS SERVICE
// ============================================================================

class AnalyticsService {
  static trackScreenView(screenName) {
    console.log(`Screen viewed: ${screenName}`);
    // Implement Firebase Analytics here
  }
  
  static trackAnalysisStart(userProfile) {
    console.log('Analysis started:', userProfile);
    // Track analysis initiation
  }
  
  static trackAnalysisComplete(results) {
    console.log('Analysis completed:', results.scores.overall);
    // Track completion with score
  }
  
  static trackPaywallView(trigger) {
    console.log('Paywall viewed:', trigger);
    // Track paywall impressions
  }
  
  static trackPurchase(productId, price) {
    console.log('Purchase:', productId, price);
    // Track conversions
  }

  static trackShare(source) {
    console.log('Content shared from:', source);
    // Track viral sharing
  }
}

// ============================================================================
// COMPONENTS
// ============================================================================

// Enhanced Input Screen with Professional Focus
const InputScreen = ({ navigation }) => {
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    company: '',
    title: '',
  });
  const [focusedField, setFocusedField] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAnalyze = async () => {
    if (!formData.name.trim() || !formData.location.trim()) {
      Alert.alert(
        'Missing Information',
        'Please enter both your name and location to continue.',
        [{ text: 'OK' }]
      );
      return;
    }

    AnalyticsService.trackAnalysisStart(formData);
    setIsLoading(true);
    
    try {
      navigation.navigate('Loading', { formData });
    } catch (error) {
      setIsLoading(false);
      Alert.alert(
        'Analysis Failed',
        'Unable to start analysis. Please try again.',
        [{ text: 'OK' }]
      );
    }
  };

  const isFormValid = formData.name.trim() && formData.location.trim();

  useEffect(() => {
    AnalyticsService.trackScreenView('InputScreen');
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContainer}
          showsVerticalScrollIndicator={false}
        >
          {/* Header Section */}
          <View style={styles.card}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
              <Icon name="search" size={32} color={colors.blue400} />
              <Text style={[styles.title, { marginLeft: 8 }]}>RepRead</Text>
            </View>
            <Text style={styles.subtitle}>See what AI knows about you</Text>
            <Text style={styles.description}>
              Discover how ChatGPT, Claude, and Gemini represent you when colleagues 
              and clients search your name. Get actionable insights to enhance your 
              professional reputation.
            </Text>
          </View>

          {/* Main Form Card */}
          <View style={styles.card}>
            <Text style={[styles.sectionTitle, { textAlign: 'center', marginBottom: 24 }]}>
              Check Your Professional Presence
            </Text>

            {/* Name Input */}
            <View style={{ marginBottom: 24 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                <Icon name="person" size={16} color={colors.gray200} />
                <Text style={[styles.label, { marginLeft: 8, marginBottom: 0 }]}>
                  Full Name *
                </Text>
              </View>
              <TextInput
                style={[
                  styles.input,
                  focusedField === 'name' && styles.inputFocused
                ]}
                value={formData.name}
                onChangeText={(value) => handleInputChange('name', value)}
                placeholder="Sarah Johnson"
                placeholderTextColor={colors.gray400}
                onFocus={() => setFocusedField('name')}
                onBlur={() => setFocusedField(null)}
                autoCapitalize="words"
                autoCorrect={false}
              />
            </View>

            {/* Location Input */}
            <View style={{ marginBottom: 24 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                <Icon name="location-on" size={16} color={colors.gray200} />
                <Text style={[styles.label, { marginLeft: 8, marginBottom: 0 }]}>
                  City, State *
                </Text>
              </View>
              <TextInput
                style={[
                  styles.input,
                  focusedField === 'location' && styles.inputFocused
                ]}
                value={formData.location}
                onChangeText={(value) => handleInputChange('location', value)}
                placeholder="San Francisco, CA"
                placeholderTextColor={colors.gray400}
                onFocus={() => setFocusedField('location')}
                onBlur={() => setFocusedField(null)}
                autoCapitalize="words"
                autoCorrect={false}
              />
            </View>

            {/* Company Input */}
            <View style={{ marginBottom: 24 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                <Icon name="business" size={16} color={colors.gray200} />
                <Text style={[styles.label, { marginLeft: 8, marginBottom: 0 }]}>
                  Current Company
                </Text>
              </View>
              <TextInput
                style={[
                  styles.input,
                  focusedField === 'company' && styles.inputFocused
                ]}
                value={formData.company}
                onChangeText={(value) => handleInputChange('company', value)}
                placeholder="Acme Corporation"
                placeholderTextColor={colors.gray400}
                onFocus={() => setFocusedField('company')}
                onBlur={() => setFocusedField(null)}
                autoCapitalize="words"
                autoCorrect={false}
              />
            </View>

            {/* Title Input */}
            <View style={{ marginBottom: 24 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                <Icon name="work" size={16} color={colors.gray200} />
                <Text style={[styles.label, { marginLeft: 8, marginBottom: 0 }]}>
                  Job Title
                </Text>
              </View>
              <TextInput
                style={[
                  styles.input,
                  focusedField === 'title' && styles.inputFocused
                ]}
                value={formData.title}
                onChangeText={(value) => handleInputChange('title', value)}
                placeholder="Senior Director"
                placeholderTextColor={colors.gray400}
                onFocus={() => setFocusedField('title')}
                onBlur={() => setFocusedField(null)}
                autoCapitalize="words"
                autoCorrect={false}
              />
            </View>

            {/* Submit Button */}
            <TouchableOpacity
              style={[
                styles.primaryButton,
                !isFormValid && styles.primaryButtonDisabled
              ]}
              onPress={handleAnalyze}
              disabled={!isFormValid || isLoading}
              activeOpacity={0.8}
            >
              <Icon 
                name="search" 
                size={20} 
                color={colors.white} 
                style={{ marginRight: 8 }} 
              />
              <Text style={styles.buttonText}>
                {isLoading ? 'Starting Analysis...' : 'Analyze My Reputation'}
              </Text>
            </TouchableOpacity>

            {/* Privacy Notice */}
            <View style={{ 
              flexDirection: 'row', 
              alignItems: 'center', 
              justifyContent: 'center',
              marginTop: 16,
              padding: 12,
              backgroundColor: colors.gray700,
              borderRadius: 8
            }}>
              <Icon name="lock" size={16} color={colors.green400} style={{ marginRight: 8 }} />
              <Text style={{ fontSize: 12, color: colors.gray300, textAlign: 'center' }}>
                Your data is analyzed securely and never stored permanently
              </Text>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

// Enhanced Loading Screen with Real-time Query Visualization
const LoadingScreen = ({ route, navigation }) => {
  const { formData } = route.params;
  const [queryProgress, setQueryProgress] = useState({
    gpt4: { completed: 0, total: 15, current: '' },
    claude: { completed: 0, total: 15, current: '' },
    gemini: { completed: 0, total: 12, current: '' },
    perplexity: { completed: 0, total: 10, current: '' }
  });
  const [totalQueries] = useState(52);
  const [completedQueries, setCompletedQueries] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('Initializing analysis...');

  const aiServices = {
    gpt4: { name: 'ChatGPT-4', icon: '🤖', color: colors.green400 },
    claude: { name: 'Claude', icon: '🧠', color: colors.yellow400 },
    gemini: { name: 'Gemini', icon: '💎', color: colors.blue400 },
    perplexity: { name: 'Perplexity', icon: '🔍', color: '#8b5cf6' }
  };

  const queries = {
    basic: [
      `${formData.name}`,
      `Who is ${formData.name}?`,
      `${formData.name} biography`,
      `Tell me about ${formData.name}`
    ],
    professional: [
      `${formData.name} professional background`,
      `${formData.name} career`,
      `${formData.name} work experience`,
      `${formData.name} achievements`
    ],
    contextual: formData.company ? [
      `${formData.name} ${formData.company}`,
      `${formData.name} at ${formData.company}`,
      `${formData.name} ${formData.location}`,
      `${formData.name} ${formData.title || 'professional'}`
    ] : [
      `${formData.name} ${formData.location}`,
      `${formData.name} professional ${formData.location}`,
      `${formData.name} ${formData.title || 'expert'}`,
      `${formData.name} current role`
    ]
  };

  useEffect(() => {
    AnalyticsService.trackScreenView('LoadingScreen');
    simulateAnalysis();
  }, []);

  const simulateAnalysis = async () => {
    const allQueries = [...queries.basic, ...queries.professional, ...queries.contextual];
    let queryIndex = 0;
    let completed = 0;

    // Phase 1: Query Generation
    setCurrentPhase('Generating targeted search queries...');
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Phase 2: Execute queries
    setCurrentPhase('Executing multi-AI analysis...');
    
    const serviceKeys = Object.keys(aiServices);
    for (const serviceKey of serviceKeys) {
      const service = aiServices[serviceKey];
      const serviceQueries = allQueries.slice(0, queryProgress[serviceKey].total);
      
      setQueryProgress(prev => ({
        ...prev,
        [serviceKey]: { ...prev[serviceKey], current: `Starting ${service.name} analysis...` }
      }));

      for (let i = 0; i < serviceQueries.length; i++) {
        const query = serviceQueries[i];
        
        setQueryProgress(prev => ({
          ...prev,
          [serviceKey]: { 
            ...prev[serviceKey], 
            current: query,
            completed: i + 1
          }
        }));

        completed++;
        setCompletedQueries(completed);

        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
      }

      setQueryProgress(prev => ({
        ...prev,
        [serviceKey]: { ...prev[serviceKey], current: '' }
      }));
    }

    // Phase 3: Analysis
    setCurrentPhase('Analyzing responses and detecting patterns...');
    await new Promise(resolve => setTimeout(resolve, 2000));

    setCurrentPhase('Generating insights and recommendations...');
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Complete analysis
    try {
      const analysisData = await new APIService().analyzeReputation(formData);
      AnalyticsService.trackAnalysisComplete(analysisData);
      
      // Navigate to paywall for freemium model
      navigation.replace('Paywall', { 
        analysisData: {
          ...analysisData,
          isBasicScan: true,
          queriesFound: completed,
          platformsFound: analysisData.platformsFound
        }, 
        formData 
      });
      
    } catch (error) {
      console.error('Analysis failed:', error);
      navigation.goBack();
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.loadingContainer}>
        {/* Overall Progress Header */}
        <View style={styles.progressHeader}>
          <Text style={styles.loadingTitle}>Analyzing Your AI Presence</Text>
          <Text style={styles.progressCounter}>
            {completedQueries} of {totalQueries} queries completed
          </Text>
          
          <View style={styles.overallProgressBar}>
            <View 
              style={[
                styles.overallProgressFill,
                { width: `${(completedQueries / totalQueries) * 100}%` }
              ]} 
            />
          </View>
          
          <Text style={{ fontSize: 14, color: colors.gray400, marginTop: 8, textAlign: 'center' }}>
            {currentPhase}
          </Text>
        </View>

        {/* Live Query Feed */}
        <View style={styles.liveQueryFeed}>
          <Text style={styles.sectionTitle}>Live Query Analysis</Text>
          
          {Object.entries(aiServices).map(([key, service]) => {
            const progress = queryProgress[key];
            const isActive = progress.current !== '';
            const progressPercent = progress.total > 0 ? (progress.completed / progress.total) * 100 : 0;
            
            return (
              <View key={key} style={[
                styles.queryServiceCard,
                isActive && styles.queryServiceCardActive
              ]}>
                <View style={styles.serviceHeader}>
                  <Text style={styles.serviceIcon}>{service.icon}</Text>
                  <View style={styles.serviceInfo}>
                    <Text style={styles.serviceName}>{service.name}</Text>
                    <Text style={styles.serviceProgress}>
                      {progress.completed}/{progress.total} queries
                    </Text>
                  </View>
                  {isActive && (
                    <ActivityIndicator size="small" color={service.color} />
                  )}
                </View>
                
                {isActive && (
                  <View style={styles.currentQuery}>
                    <Text style={styles.currentQueryText}>
                      "{progress.current}"
                    </Text>
                  </View>
                )}
                
                <View style={styles.serviceProgressBar}>
                  <View 
                    style={[
                      styles.serviceProgressFill,
                      { 
                        width: `${progressPercent}%`,
                        backgroundColor: service.color
                      }
                    ]} 
                  />
                </View>
              </View>
            );
          })}
        </View>

        {/* Query Categories Breakdown */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Analysis Scope</Text>
          
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
            <CategoryItem 
              icon="🔍"
              title="Identity Queries"
              count="16"
              description="Basic name recognition"
            />
            <CategoryItem 
              icon="🏢"
              title="Professional Context"
              count="20"
              description="Role & company association"
            />
            <CategoryItem 
              icon="📍"
              title="Location-Based"
              count="8"
              description="Geographic context"
            />
            <CategoryItem 
              icon="📰"
              title="Recent Activity"
              count="8"
              description="Current mentions & news"
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const CategoryItem = ({ icon, title, count, description }) => (
  <View style={{ 
    width: '48%', 
    backgroundColor: colors.gray700, 
    borderRadius: 12, 
    padding: 16, 
    marginBottom: 12,
    alignItems: 'center'
  }}>
    <Text style={{ fontSize: 24, marginBottom: 8 }}>{icon}</Text>
    <Text style={{ fontSize: 14, fontWeight: '600', color: colors.white, textAlign: 'center', marginBottom: 4 }}>
      {title}
    </Text>
    <Text style={{ fontSize: 16, fontWeight: 'bold', color: colors.blue400, marginBottom: 4 }}>
      {count} queries
    </Text>
    <Text style={{ fontSize: 12, color: colors.gray400, textAlign: 'center' }}>
      {description}
    </Text>
  </View>
);

// Freemium Paywall Screen
const PaywallScreen = ({ route, navigation }) => {
  const { analysisData, formData } = route.params;
  const [selectedOption, setSelectedOption] = useState('single');

  useEffect(() => {
    AnalyticsService.trackPaywallView('analysis_complete');
  }, []);

  const handlePurchase = (productId) => {
    AnalyticsService.trackPurchase(productId, productId === 'single' ? 4.99 : 19.99);
    
    Alert.alert(
      'Purchase Initiated',
      `Processing ${productId === 'single' ? 'single analysis' : 'Pro subscription'} purchase...`,
      [
        { 
          text: 'OK', 
          onPress: () => {
            // Navigate to full results
            navigation.replace('Results', { 
              analysisData: { ...analysisData, isBasicScan: false },
              formData 
            });
          }
        }
      ]
    );
  };

  const handleFreeContinue = () => {
    // Show basic results only
    navigation.replace('Results', { 
      analysisData: { ...analysisData, isBasicScan: true },
      formData 
    });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.paywallContainer}>
        <Text style={styles.paywallTitle}>Want the Complete Analysis?</Text>
        
        <View style={{ backgroundColor: colors.gray800, borderRadius: 16, padding: 20, marginBottom: 32 }}>
          <Text style={{ fontSize: 18, fontWeight: '600', color: colors.white, textAlign: 'center', marginBottom: 12 }}>
            Your Basic Scan Results
          </Text>
          <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginBottom: 16 }}>
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.green400 }}>
                {analysisData.platformsFound}/4
              </Text>
              <Text style={{ fontSize: 12, color: colors.gray400 }}>AI Platforms Found You</Text>
            </View>
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.blue400 }}>
                {analysisData.queriesFound}
              </Text>
              <Text style={{ fontSize: 12, color: colors.gray400 }}>Queries Executed</Text>
            </View>
            <View style={{ alignItems: 'center' }}>
              <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.yellow400 }}>
                {analysisData.scores.overall}
              </Text>
              <Text style={{ fontSize: 12, color: colors.gray400 }}>Overall Score</Text>
            </View>
          </View>
          
          <TouchableOpacity 
            style={{ 
              backgroundColor: colors.gray700, 
              padding: 12, 
              borderRadius: 8, 
              alignItems: 'center' 
            }}
            onPress={handleFreeContinue}
          >
            <Text style={{ color: colors.gray300, fontSize: 14 }}>
              Continue with Basic Results
            </Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.paywallDescription}>
          Unlock detailed insights, word cloud analysis, discrepancy detection, 
          and personalized recommendations to enhance your AI reputation.
        </Text>

        <View style={styles.pricingContainer}>
          <TouchableOpacity 
            style={[
              styles.pricingOption,
              selectedOption === 'single' && styles.pricingOptionSelected
            ]}
            onPress={() => setSelectedOption('single')}
          >
            <Text style={styles.pricingTitle}>Complete Analysis</Text>
            <Text style={styles.pricingPrice}>$4.99</Text>
            <Text style={styles.pricingDescription}>
              • Full 52-query analysis across all AI platforms{'\n'}
              • Word cloud visualization of AI knowledge{'\n'}
              • Discrepancy detection and recommendations{'\n'}
              • Shareable professional report
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[
              styles.pricingOption,
              selectedOption === 'pro' && styles.pricingOptionSelected
            ]}
            onPress={() => setSelectedOption('pro')}
          >
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <Text style={styles.pricingTitle}>RepRead Pro</Text>
              <View style={{ backgroundColor: colors.blue600, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 }}>
                <Text style={{ color: colors.white, fontSize: 12, fontWeight: '600' }}>BEST VALUE</Text>
              </View>
            </View>
            <Text style={styles.pricingPrice}>$19.99/month</Text>
            <Text style={styles.pricingDescription}>
              • Unlimited reputation scans{'\n'}
              • Monthly monitoring with alerts{'\n'}
              • Advanced analytics and trends{'\n'}
              • Priority customer support{'\n'}
              • Export capabilities for presentations
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => handlePurchase(selectedOption)}
        >
          <Text style={styles.buttonText}>
            {selectedOption === 'single' ? 'Unlock Complete Analysis' : 'Start Pro Subscription'}
          </Text>
          <Icon name="arrow-forward" size={16} color={colors.white} style={{ marginLeft: 8 }} />
        </TouchableOpacity>

        <Text style={{ fontSize: 12, color: colors.gray400, textAlign: 'center', marginTop: 16 }}>
          Secure payment • Cancel anytime • 30-day money-back guarantee
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
};

// Word Cloud Component
const AIKnowledgeWordCloud = ({ analysisData }) => {
  const [selectedWord, setSelectedWord] = useState(null);

  return (
    <View style={styles.wordCloudContainer}>
      <Text style={styles.sectionTitle}>What AI Associates With You</Text>
      <Text style={styles.wordCloudSubtitle}>
        Size = frequency • Color = AI consensus level
      </Text>
      
      <View style={styles.wordCloudCanvas}>
        {analysisData.wordCloud.slice(0, 20).map((item, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.wordItem,
              {
                position: 'absolute',
                left: item.x,
                top: item.y,
              }
            ]}
            onPress={() => setSelectedWord(item)}
          >
            <Text style={[
              styles.wordText,
              {
                fontSize: item.size,
                color: item.color,
                fontWeight: item.count > 10 ? 'bold' : 'normal'
              }
            ]}>
              {item.word}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      
      {/* Legend */}
      <View style={styles.wordCloudLegend}>
        <LegendItem color={colors.green400} label="All AI platforms" />
        <LegendItem color={colors.blue400} label="Most AI platforms" />
        <LegendItem color={colors.yellow400} label="Some AI platforms" />
        <LegendItem color={colors.gray400} label="Single platform" />
      </View>
      
      {/* Word Detail Modal */}
      {selectedWord && (
        <Modal transparent visible={true} animationType="fade">
          <View style={styles.modalOverlay}>
            <View style={styles.wordDetailModal}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>"{selectedWord.word}"</Text>
                <TouchableOpacity onPress={() => setSelectedWord(null)}>
                  <Icon name="close" size={24} color={colors.gray400} />
                </TouchableOpacity>
              </View>
              
              <Text style={{ fontSize: 16, color: colors.gray300, marginBottom: 16 }}>
                Mentioned {selectedWord.count} times across {selectedWord.sources.length} AI platform{selectedWord.sources.length > 1 ? 's' : ''}
              </Text>
              
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                {selectedWord.sources.map(source => (
                  <View key={source} style={{ 
                    backgroundColor: colors.gray700, 
                    paddingHorizontal: 12, 
                    paddingVertical: 6, 
                    borderRadius: 16 
                  }}>
                    <Text style={{ color: colors.white, fontSize: 12 }}>{source}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
};

const LegendItem = ({ color, label }) => (
  <View style={styles.legendItem}>
    <View style={[styles.legendColor, { backgroundColor: color }]} />
    <Text style={styles.legendLabel}>{label}</Text>
  </View>
);

// Results Screen with Tabbed Interface
const ResultsScreen = ({ route, navigation }) => {
  const { analysisData, formData } = route.params;
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', title: 'Overview', icon: 'dashboard' },
    { id: 'knowledge', title: 'AI Knowledge', icon: 'psychology' },
    { id: 'discrepancies', title: 'Discrepancies', icon: 'compare_arrows' },
    { id: 'recommendations', title: 'Action Plan', icon: 'lightbulb' }
  ];

  useEffect(() => {
    AnalyticsService.trackScreenView('ResultsScreen');
  }, []);

  const shareResults = async () => {
    const message = `I just checked my AI reputation with RepRead! AI platforms gave me a ${analysisData.scores.overall}/100 professional visibility score. Check yours at RepRead!`;
    
    try {
      await Share.share({
        message,
        title: 'My AI Reputation Report',
      });
      AnalyticsService.trackShare('results_screen');
    } catch (error) {
      console.log('Share cancelled or failed:', error);
    }
  };

  const ReputationScore = ({ score, category }) => (
    <View style={styles.scoreContainer}>
      <Text style={[
        styles.scoreValue,
        score >= 80 ? styles.scoreHigh : score >= 60 ? styles.scoreMedium : styles.scoreLow
      ]}>
        {score}
      </Text>
      <Text style={styles.scoreLabel}>{category}</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Header */}
      <View style={{ backgroundColor: colors.gray800, padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <View>
          <Text style={{ fontSize: 20, fontWeight: 'bold', color: colors.white }}>
            AI Reputation Report
          </Text>
          <Text style={{ fontSize: 14, color: colors.gray400 }}>
            for {formData.name}
          </Text>
        </View>
        
        <View style={{ flexDirection: 'row', gap: 12 }}>
          <TouchableOpacity onPress={shareResults}>
            <Icon name="share" size={24} color={colors.blue400} />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Icon name="refresh" size={24} color={colors.gray400} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Tab Navigation */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ backgroundColor: colors.gray800 }}>
        <View style={styles.tabNavigation}>
          {tabs.map(tab => (
            <TouchableOpacity
              key={tab.id}
              style={[
                styles.tab,
                activeTab === tab.id && styles.activeTab
              ]}
              onPress={() => setActiveTab(tab.id)}
            >
              <Icon 
                name={tab.icon} 
                size={16} 
                color={activeTab === tab.id ? colors.white : colors.gray400} 
              />
              <Text style={[
                styles.tabTitle,
                activeTab === tab.id && styles.activeTabTitle
              ]}>
                {tab.title}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
      
      <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16 }}>
        {activeTab === 'overview' && (
          <View>
            {/* Reputation Scores */}
            <View style={styles.card}>
              <Text style={[styles.sectionTitle, { marginBottom: 24, textAlign: 'center' }]}>
                Your AI Reputation Score
              </Text>
              <View style={styles.grid}>
                <View style={styles.gridItem}>
                  <ReputationScore score={analysisData.scores.overall} category="Overall" />
                </View>
                <View style={styles.gridItem}>
                  <ReputationScore score={analysisData.scores.professional} category="Professional" />
                </View>
                <View style={styles.gridItem}>
                  <ReputationScore score={analysisData.scores.visibility} category="Visibility" />
                </View>
                <View style={styles.gridItem}>
                  <ReputationScore score={analysisData.scores.accuracy} category="Accuracy" />
                </View>
              </View>

              {analysisData.scores.overall < 80 && (
                <View style={{
                  backgroundColor: colors.yellow400 + '20',
                  borderColor: colors.yellow400,
                  borderWidth: 1,
                  borderRadius: 12,
                  padding: 16,
                  flexDirection: 'row',
                  alignItems: 'flex-start',
                  marginTop: 16
                }}>
                  <Icon name="warning" size={20} color={colors.yellow400} style={{ marginRight: 12, marginTop: 2 }} />
                  <View style={{ flex: 1 }}>
                    <Text style={{ fontSize: 16, fontWeight: '600', color: colors.yellow400, marginBottom: 4 }}>
                      Enhancement Opportunity
                    </Text>
                    <Text style={{ fontSize: 14, color: colors.yellow400 }}>
                      Your visibility score shows room for growth. AI assistants are finding limited recent information about you.
                    </Text>
                  </View>
                </View>
              )}
            </View>

            {/* Query Statistics */}
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Analysis Summary</Text>
              <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
                <View style={{ alignItems: 'center' }}>
                  <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.blue400 }}>
                    {analysisData.queryStats.totalQueries}
                  </Text>
                  <Text style={{ fontSize: 12, color: colors.gray400 }}>Total Queries</Text>
                </View>
                <View style={{ alignItems: 'center' }}>
                  <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.green400 }}>
                    {analysisData.queryStats.aiPlatforms}
                  </Text>
                  <Text style={{ fontSize: 12, color: colors.gray400 }}>AI Platforms</Text>
                </View>
                <View style={{ alignItems: 'center' }}>
                  <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.yellow400 }}>
                    {analysisData.platformsFound}
                  </Text>
                  <Text style={{ fontSize: 12, color: colors.gray400 }}>Found You</Text>
                </View>
              </View>
            </View>
          </View>
        )}
        
        {activeTab === 'knowledge' && !analysisData.isBasicScan && (
          <AIKnowledgeWordCloud analysisData={analysisData} />
        )}
        
        {activeTab === 'knowledge' && analysisData.isBasicScan && (
          <View style={styles.card}>
            <Icon name="lock" size={48} color={colors.gray500} style={{ alignSelf: 'center', marginBottom: 16 }} />
            <Text style={[styles.sectionTitle, { textAlign: 'center' }]}>
              Word Cloud Analysis
            </Text>
            <Text style={[styles.description, { marginBottom: 24 }]}>
              Upgrade to see what words AI most strongly associates with your name, 
              sized by frequency and colored by consensus across platforms.
            </Text>
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.buttonText}>Upgrade to Pro</Text>
            </TouchableOpacity>
          </View>
        )}
        
        {activeTab === 'recommendations' && (
          <View>
            <Text style={styles.sectionTitle}>Personalized Action Plan</Text>
            <Text style={[styles.description, { textAlign: 'left', marginBottom: 24 }]}>
              Ranked by impact potential for your professional reputation
            </Text>
            
            {analysisData.recommendations.map((rec, index) => (
              <View key={index} style={styles.card}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <Text style={{ fontSize: 16, fontWeight: '600', color: colors.white, flex: 1 }}>
                    {rec.title}
                  </Text>
                  {rec.automated && <Icon name="flash-on" size={16} color={colors.yellow400} />}
                </View>
                
                <Text style={{ fontSize: 14, color: colors.gray400, marginBottom: 12 }}>
                  {rec.description}
                </Text>
                
                <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
                  <View style={{ 
                    backgroundColor: rec.impact === 'high' ? colors.green400 + '20' : rec.impact === 'medium' ? colors.yellow400 + '20' : colors.blue400 + '20',
                    borderColor: rec.impact === 'high' ? colors.green400 : rec.impact === 'medium' ? colors.yellow400 : colors.blue400,
                    borderWidth: 1,
                    paddingHorizontal: 8, 
                    paddingVertical: 4, 
                    borderRadius: 12 
                  }}>
                    <Text style={{ 
                      color: rec.impact === 'high' ? colors.green400 : rec.impact === 'medium' ? colors.yellow400 : colors.blue400,
                      fontSize: 12, 
                      fontWeight: '600' 
                    }}>
                      {rec.impact} impact
                    </Text>
                  </View>
                  <View style={{ 
                    backgroundColor: rec.effort === 'low' ? colors.green400 + '20' : rec.effort === 'medium' ? colors.yellow400 + '20' : colors.red400 + '20',
                    borderColor: rec.effort === 'low' ? colors.green400 : rec.effort === 'medium' ? colors.yellow400 : colors.red400,
                    borderWidth: 1,
                    paddingHorizontal: 8, 
                    paddingVertical: 4, 
                    borderRadius: 12 
                  }}>
                    <Text style={{ 
                      color: rec.effort === 'low' ? colors.green400 : rec.effort === 'medium' ? colors.yellow400 : colors.red400,
                      fontSize: 12, 
                      fontWeight: '600' 
                    }}>
                      {rec.effort} effort
                    </Text>
                  </View>
                </View>
                
                <TouchableOpacity style={{ alignSelf: 'flex-start' }}>
                  <Text style={{ color: colors.blue400, fontSize: 14, fontWeight: '600' }}>
                    {rec.automated ? 'Auto-fix →' : 'Get guide →'}
                  </Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

// Main App Component with Navigation
const Stack = createStackNavigator();

const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator 
        initialRouteName="Input"
        screenOptions={{
          headerShown: false,
          cardStyle: { backgroundColor: colors.gray900 }
        }}
      >
        <Stack.Screen name="Input" component={InputScreen} />
        <Stack.Screen name="Loading" component={LoadingScreen} />
        <Stack.Screen name="Paywall" component={PaywallScreen} />
        <Stack.Screen name="Results" component={ResultsScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;
