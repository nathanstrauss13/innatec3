import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  SafeAreaView,
  ActivityIndicator,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { styles, colors } from '../styles/styles';
import { analyzeReputation } from '../services/api';

const LoadingScreen = ({ route, navigation }) => {
  const { formData } = route.params;
  const [currentStep, setCurrentStep] = useState(0);
  const [fadeAnim] = useState(new Animated.Value(0));

  const steps = [
    {
      id: 0,
      text: 'Generating search queries...',
      icon: 'settings',
      completed: false,
    },
    {
      id: 1,
      text: 'Analyzing AI responses...',
      icon: 'psychology',
      completed: false,
    },
    {
      id: 2,
      text: 'Generating recommendations...',
      icon: 'lightbulb',
      completed: false,
    },
  ];

  const [progressSteps, setProgressSteps] = useState(steps);

  useEffect(() => {
    // Start fade in animation
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();

    // Simulate progress steps
    const progressTimer = setInterval(() => {
      setCurrentStep(prev => {
        const nextStep = prev + 1;
        
        // Update progress steps
        setProgressSteps(prevSteps => 
          prevSteps.map((step, index) => ({
            ...step,
            completed: index < nextStep
          }))
        );

        if (nextStep >= steps.length) {
          clearInterval(progressTimer);
          // Start the actual API call
          performAnalysis();
        }
        
        return nextStep;
      });
    }, 1500); // 1.5 seconds per step

    return () => clearInterval(progressTimer);
  }, []);

  const performAnalysis = async () => {
    try {
      const analysisData = await analyzeReputation(formData);
      
      // Wait a moment to show completion
      setTimeout(() => {
        navigation.replace('Results', { analysisData, formData });
      }, 1000);
      
    } catch (error) {
      console.error('Analysis failed:', error);
      navigation.goBack();
      // Error will be handled by InputScreen
    }
  };

  const getStepIcon = (step, index) => {
    if (step.completed) {
      return <Icon name="check-circle" size={16} color={colors.green400} />;
    } else if (index === currentStep) {
      return (
        <ActivityIndicator 
          size="small" 
          color={colors.blue500} 
          style={{ width: 16, height: 16 }}
        />
      );
    } else {
      return (
        <View 
          style={{
            width: 16,
            height: 16,
            borderRadius: 8,
            borderWidth: 2,
            borderColor: colors.gray700,
          }}
        />
      );
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <Animated.View style={[styles.loadingContainer, { opacity: fadeAnim }]}>
        {/* Main Loading Spinner */}
        <ActivityIndicator 
          size="large" 
          color={colors.blue500} 
          style={styles.loadingSpinner}
        />
        
        {/* Loading Title */}
        <Text style={styles.loadingTitle}>
          Analyzing your AI presence...
        </Text>
        
        {/* Loading Description */}
        <Text style={styles.loadingDescription}>
          Checking ChatGPT, Claude, Gemini, and search engines
        </Text>
        
        {/* Progress Steps */}
        <View style={styles.progressContainer}>
          {progressSteps.map((step, index) => (
            <View 
              key={step.id}
              style={[
                styles.progressItem,
                step.completed && styles.progressItemCompleted
              ]}
            >
              <Text style={styles.progressText}>{step.text}</Text>
              {getStepIcon(step, index)}
            </View>
          ))}
        </View>
      </Animated.View>
    </SafeAreaView>
  );
};

export default LoadingScreen;
