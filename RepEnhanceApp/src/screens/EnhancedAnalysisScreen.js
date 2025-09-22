import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  SafeAreaView,
  ScrollView,
  ActivityIndicator,
  Animated,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { styles, colors } from '../styles/styles';

const EnhancedAnalysisScreen = ({ route, navigation }) => {
  const { formData } = route.params;
  const [currentPhase, setCurrentPhase] = useState('initialization');
  const [aiProgress, setAiProgress] = useState({
    gpt4: { status: 'pending', queries: 0, total: 4, responses: [], confidence: 'high' },
    claude: { status: 'pending', queries: 0, total: 4, responses: [], confidence: 'high' },
    gemini: { status: 'pending', queries: 0, total: 3, responses: [], confidence: 'medium' },
    perplexity: { status: 'pending', queries: 0, total: 3, responses: [], confidence: 'high' }
  });
  const [currentQuery, setCurrentQuery] = useState('');
  const [consistencyIssues, setConsistencyIssues] = useState([]);
  const [fadeAnim] = useState(new Animated.Value(0));

  const phases = [
    { id: 'initialization', name: 'Initializing Analysis', duration: 1000 },
    { id: 'multi_ai_queries', name: 'Multi-AI Testing', duration: 8000 },
    { id: 'consistency_check', name: 'Consistency Analysis', duration: 2000 },
    { id: 'sentiment_analysis', name: 'Sentiment Scoring', duration: 1500 },
    { id: 'source_attribution', name: 'Source Attribution', duration: 2000 },
    { id: 'gap_analysis', name: 'Content Gap Analysis', duration: 1500 },
    { id: 'recommendations', name: 'Generating Recommendations', duration: 2000 }
  ];

  const aiServices = {
    gpt4: {
      name: 'ChatGPT-4',
      icon: '🤖',
      color: '#10b981',
      queries: [
        `Tell me about ${formData.name}`,
        `Who is ${formData.name}?`,
        `${formData.name} professional background`,
        `${formData.name} from ${formData.location}`
      ]
    },
    claude: {
      name: 'Claude',
      icon: '🧠',
      color: '#f59e0b',
      queries: [
        `${formData.name} biography`,
        `${formData.name} from ${formData.location}`,
        `${formData.name} career information`,
        `${formData.name} at ${formData.affiliation}`
      ]
    },
    gemini: {
      name: 'Gemini',
      icon: '💎',
      color: '#3b82f6',
      queries: [
        `${formData.name} information`,
        `${formData.name} ${formData.affiliation}`,
        `${formData.name} achievements`
      ]
    },
    perplexity: {
      name: 'Perplexity',
      icon: '🔍',
      color: '#8b5cf6',
      queries: [
        `${formData.name} recent news`,
        `${formData.name} current role`,
        `${formData.name} publications`
      ]
    }
  };

  useEffect(() => {
    startAnalysis();
  }, []);

  const startAnalysis = async () => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();

    for (const phase of phases) {
      setCurrentPhase(phase.id);
      
      if (phase.id === 'multi_ai_queries') {
        await runMultiAIQueries();
      } else if (phase.id === 'consistency_check') {
        await runConsistencyCheck();
      } else {
        await new Promise(resolve => setTimeout(resolve, phase.duration));
      }
    }

    // Navigate to enhanced results
    navigation.replace('EnhancedResults', { 
      formData, 
      analysisData: generateEnhancedResults() 
    });
  };

  const runMultiAIQueries = async () => {
    const services = Object.keys(aiServices);
    
    for (const serviceKey of services) {
      const service = aiServices[serviceKey];
      setAiProgress(prev => ({
        ...prev,
        [serviceKey]: { ...prev[serviceKey], status: 'running' }
      }));

      for (let i = 0; i < service.queries.length; i++) {
        const query = service.queries[i];
        setCurrentQuery(`${service.name}: ${query}`);
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Mock response
        const mockResponse = generateMockResponse(query, formData);
        
        setAiProgress(prev => ({
          ...prev,
          [serviceKey]: {
            ...prev[serviceKey],
            queries: i + 1,
            responses: [...prev[serviceKey].responses, { query, response: mockResponse }]
          }
        }));
      }

      setAiProgress(prev => ({
        ...prev,
        [serviceKey]: { ...prev[serviceKey], status: 'completed' }
      }));
    }
  };

  const runConsistencyCheck = async () => {
    setCurrentQuery('Analyzing consistency across AI responses...');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock consistency issues
    const issues = [
      { type: 'title_discrepancy', severity: 'medium', description: 'Job title varies between sources' },
      { type: 'location_conflict', severity: 'low', description: 'Minor location formatting differences' }
    ];
    setConsistencyIssues(issues);
    
    setCurrentQuery('Cross-referencing information sources...');
    await new Promise(resolve => setTimeout(resolve, 1000));
  };

  const generateMockResponse = (query, formData) => {
    const responses = [
      `${formData.name} is a professional based in ${formData.location}, associated with ${formData.affiliation}.`,
      `I found some information about ${formData.name}, including their work at ${formData.affiliation}.`,
      `${formData.name} appears to be known for their contributions in their field.`,
      `Based on available information, ${formData.name} has a professional presence online.`,
      `I don't have comprehensive information about ${formData.name} in my current dataset.`
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const generateEnhancedResults = () => {
    return {
      timestamp: new Date().toISOString(),
      person: formData,
      scores: {
        overall: Math.floor(Math.random() * 30) + 70,
        professional: Math.floor(Math.random() * 25) + 75,
        visibility: Math.floor(Math.random() * 40) + 45,
        accuracy: Math.floor(Math.random() * 20) + 65,
        consistency: Math.floor(Math.random() * 20) + 75
      },
      aiAnalysis: aiProgress,
      consistencyIssues,
      sentimentAnalysis: {
        overall: 'positive',
        professional: 0.85,
        personal: 0.72,
        trend: 'stable',
        themes: ['professional', 'expertise', 'leadership']
      },
      sourceAttribution: {
        linkedin: { weight: 0.4, found: true, quality: 'high' },
        news: { weight: 0.3, found: false, quality: 'none' },
        company: { weight: 0.25, found: true, quality: 'medium' },
        social: { weight: 0.15, found: true, quality: 'low' }
      },
      contentGaps: {
        missing: ['recent_projects', 'thought_leadership', 'media_coverage'],
        outdated: ['job_title', 'bio_description'],
        opportunities: ['industry_articles', 'speaking_events', 'podcast_appearances']
      },
      recommendations: [
        {
          title: 'Optimize LinkedIn Profile',
          description: 'Update headline and summary for better AI discoverability',
          impact: 'high',
          effort: 'low',
          category: 'professional_presence',
          priority: 1
        },
        {
          title: 'Create Thought Leadership Content',
          description: 'Publish articles to establish expertise and improve AI knowledge',
          impact: 'high',
          effort: 'medium',
          category: 'content_creation',
          priority: 2
        },
        {
          title: 'Update Company Bio',
          description: 'Ensure company website has current information',
          impact: 'medium',
          effort: 'low',
          category: 'source_optimization',
          priority: 3
        }
      ]
    };
  };

  const getPhaseIcon = (phaseId) => {
    const icons = {
      initialization: '⚡',
      multi_ai_queries: '🤖',
      consistency_check: '🔍',
      sentiment_analysis: '💭',
      source_attribution: '📊',
      gap_analysis: '🎯',
      recommendations: '💡'
    };
    return icons[phaseId] || '⏳';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'pending': return '⏳';
      default: return '⏳';
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Advanced AI Analysis</Text>
            <Text style={styles.subtitle}>
              Comprehensive reputation analysis for {formData.name}
            </Text>
          </View>

          {/* Current Phase */}
          <View style={styles.card}>
            <View style={styles.currentPhaseContainer}>
              <Text style={styles.currentPhaseIcon}>
                {getPhaseIcon(currentPhase)}
              </Text>
              <View style={styles.currentPhaseText}>
                <Text style={styles.currentPhaseTitle}>
                  {phases.find(p => p.id === currentPhase)?.name || 'Processing...'}
                </Text>
                <Text style={styles.currentQuery}>{currentQuery}</Text>
              </View>
            </View>
          </View>

          {/* AI Services Progress */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Multi-AI Testing Progress</Text>
            {Object.entries(aiServices).map(([key, service]) => {
              const progress = aiProgress[key];
              const progressPercent = progress.total > 0 ? (progress.queries / progress.total) * 100 : 0;
              
              return (
                <View key={key} style={styles.aiServiceItem}>
                  <View style={styles.aiServiceHeader}>
                    <View style={styles.aiServiceInfo}>
                      <Text style={styles.aiServiceIcon}>{service.icon}</Text>
                      <Text style={styles.aiServiceName}>{service.name}</Text>
                      <View style={[styles.confidenceBadge, { 
                        backgroundColor: progress.confidence === 'high' ? colors.success + '20' : colors.warning + '20',
                        borderColor: progress.confidence === 'high' ? colors.success : colors.warning
                      }]}>
                        <Text style={[styles.confidenceText, {
                          color: progress.confidence === 'high' ? colors.success : colors.warning
                        }]}>
                          {progress.confidence}
                        </Text>
                      </View>
                    </View>
                    <Text style={styles.statusIcon}>{getStatusIcon(progress.status)}</Text>
                  </View>
                  
                  <View style={styles.progressContainer}>
                    <View style={styles.progressBar}>
                      <View 
                        style={[
                          styles.progressFill, 
                          { 
                            width: `${progressPercent}%`,
                            backgroundColor: service.color
                          }
                        ]} 
                      />
                    </View>
                    <Text style={styles.progressText}>
                      {progress.queries}/{progress.total} queries
                    </Text>
                  </View>
                </View>
              );
            })}
          </View>

          {/* Analysis Phases */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Analysis Phases</Text>
            {phases.map((phase, index) => {
              const isActive = phase.id === currentPhase;
              const isCompleted = phases.findIndex(p => p.id === currentPhase) > index;
              
              return (
                <View key={phase.id} style={[
                  styles.phaseItem,
                  isActive && styles.phaseItemActive
                ]}>
                  <View style={[
                    styles.phaseIndicator,
                    isCompleted && styles.phaseIndicatorCompleted,
                    isActive && styles.phaseIndicatorActive
                  ]}>
                    <Text style={styles.phaseNumber}>
                      {isCompleted ? '✓' : index + 1}
                    </Text>
                  </View>
                  <View style={styles.phaseContent}>
                    <Text style={[
                      styles.phaseName,
                      isActive && styles.phaseNameActive
                    ]}>
                      {phase.name}
                    </Text>
                    {isActive && (
                      <ActivityIndicator 
                        size="small" 
                        color={colors.primary} 
                        style={styles.phaseSpinner}
                      />
                    )}
                  </View>
                </View>
              );
            })}
          </View>

          {/* Consistency Issues (if any) */}
          {consistencyIssues.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Consistency Analysis</Text>
              {consistencyIssues.map((issue, index) => (
                <View key={index} style={styles.consistencyIssue}>
                  <View style={[
                    styles.severityIndicator,
                    { backgroundColor: issue.severity === 'high' ? colors.error : 
                                     issue.severity === 'medium' ? colors.warning : colors.info }
                  ]} />
                  <Text style={styles.issueDescription}>{issue.description}</Text>
                </View>
              ))}
            </View>
          )}
        </ScrollView>
      </Animated.View>
    </SafeAreaView>
  );
};

export default EnhancedAnalysisScreen;
