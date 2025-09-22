import React, { useState } from 'react';
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
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { styles, colors } from '../styles/styles';
import { analyzeReputation } from '../services/api';

const InputScreen = ({ navigation }) => {
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    affiliation: '',
  });
  const [focusedField, setFocusedField] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleScan = async () => {
    if (!formData.name.trim() || !formData.location.trim()) {
      Alert.alert(
        'Missing Information',
        'Please enter both your name and location to continue.',
        [{ text: 'OK' }]
      );
      return;
    }

    setIsLoading(true);
    
    try {
      // Navigate to loading screen first
      navigation.navigate('Loading', { formData });
      
      // Perform the analysis
      const analysisData = await analyzeReputation(formData);
      
      // Navigate to results with the data
      navigation.navigate('Results', { analysisData, formData });
    } catch (error) {
      setIsLoading(false);
      Alert.alert(
        'Analysis Failed',
        error.message || 'Unable to analyze your reputation. Please try again.',
        [{ text: 'OK' }]
      );
    }
  };

  const isFormValid = formData.name.trim() && formData.location.trim();

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
          <View style={styles.cardHeader}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
              <Icon name="auto-awesome" size={32} color={colors.blue400} />
              <Text style={[styles.title, { marginLeft: 8 }]}>RepEnhance</Text>
            </View>
            <Text style={styles.subtitle}>Boost your AI reputation</Text>
            <Text style={styles.description}>
              See what ChatGPT, Claude, and Gemini find when people search for you. 
              Get actionable insights to enhance your digital presence.
            </Text>
          </View>

          {/* Main Card */}
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.iconContainer}>
                <Icon name="search" size={32} color={colors.blue400} />
              </View>
              <Text style={[styles.sectionTitle, { textAlign: 'center' }]}>
                Discover your AI footprint
              </Text>
              <Text style={styles.description}>
                We'll check what AI assistants find about you across the web
              </Text>
            </View>

            {/* Form Fields */}
            <View>
              {/* Name Input */}
              <View style={{ marginBottom: 24 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                  <Icon name="person" size={16} color={colors.gray200} />
                  <Text style={[styles.label, { marginLeft: 8, marginBottom: 0 }]}>
                    Full Name
                  </Text>
                </View>
                <TextInput
                  style={[
                    styles.input,
                    focusedField === 'name' && styles.inputFocused
                  ]}
                  value={formData.name}
                  onChangeText={(value) => handleInputChange('name', value)}
                  placeholder="e.g. Sarah Johnson"
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
                    Location
                  </Text>
                </View>
                <TextInput
                  style={[
                    styles.input,
                    focusedField === 'location' && styles.inputFocused
                  ]}
                  value={formData.location}
                  onChangeText={(value) => handleInputChange('location', value)}
                  placeholder="e.g. New York, NY"
                  placeholderTextColor={colors.gray400}
                  onFocus={() => setFocusedField('location')}
                  onBlur={() => setFocusedField(null)}
                  autoCapitalize="words"
                  autoCorrect={false}
                />
              </View>

              {/* Affiliation Input */}
              <View style={{ marginBottom: 24 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                  <Icon name="school" size={16} color={colors.gray200} />
                  <Text style={[styles.label, { marginLeft: 8, marginBottom: 0 }]}>
                    Recent Affiliation
                  </Text>
                </View>
                <TextInput
                  style={[
                    styles.input,
                    focusedField === 'affiliation' && styles.inputFocused
                  ]}
                  value={formData.affiliation}
                  onChangeText={(value) => handleInputChange('affiliation', value)}
                  placeholder="e.g. Stanford University, Google, etc."
                  placeholderTextColor={colors.gray400}
                  onFocus={() => setFocusedField('affiliation')}
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
                onPress={handleScan}
                disabled={!isFormValid || isLoading}
                activeOpacity={0.8}
              >
                <Icon 
                  name="search" 
                  size={20} 
                  color={colors.white} 
                  style={styles.iconSmall} 
                />
                <Text style={styles.buttonText}>
                  {isLoading ? 'Analyzing...' : 'Enhance My AI Reputation'}
                </Text>
              </TouchableOpacity>
            </View>

            {/* Feature Highlights */}
            <View style={styles.featureContainer}>
              <View style={styles.featureItem}>
                <Icon name="security" size={16} color={colors.gray400} />
                <Text style={styles.featureText}>Private & Secure</Text>
              </View>
              <View style={styles.featureItem}>
                <Icon name="flash-on" size={16} color={colors.gray400} />
                <Text style={styles.featureText}>Instant Results</Text>
              </View>
              <View style={styles.featureItem}>
                <Icon name="psychology" size={16} color={colors.gray400} />
                <Text style={styles.featureText}>AI-Powered</Text>
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export default InputScreen;
