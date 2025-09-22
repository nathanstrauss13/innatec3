import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { styles, colors } from '../styles/styles';
import { getRecommendationGuide } from '../services/api';

const ResultsScreen = ({ route, navigation }) => {
  const { analysisData, formData } = route.params;
  const [refreshing, setRefreshing] = useState(false);
  const [showActionDetails, setShowActionDetails] = useState({});

  const onRefresh = async () => {
    setRefreshing(true);
    // Could re-run analysis here if needed
    setTimeout(() => setRefreshing(false), 1000);
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

  const SearchQuery = ({ platform, confidence, scope }) => (
    <View style={[styles.card, { marginBottom: 12, padding: 16 }]}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <Text style={[styles.label, { marginBottom: 0 }]}>{platform}</Text>
        <View style={[
          styles.badge,
          confidence === 'high' ? styles.badgeHigh : confidence === 'medium' ? styles.badgeMedium : styles.badgeLow
        ]}>
          <Text style={[
            styles.badgeText,
            confidence === 'high' ? styles.badgeTextHigh : confidence === 'medium' ? styles.badgeTextMedium : styles.badgeTextLow
          ]}>
            {confidence} match likelihood
          </Text>
        </View>
      </View>
      <Text style={[styles.description, { textAlign: 'left', fontSize: 12 }]}>{scope}</Text>
    </View>
  );

  const ActionItem = ({ title, description, impact, effort, automated = false, actionType }) => {
    const handleActionClick = async () => {
      if (automated) {
        Alert.alert(
          'Auto-fix Initiated',
          `Auto-fix initiated for: ${title}\nThis would automatically optimize your profile settings.`,
          [{ text: 'OK' }]
        );
      } else {
        if (actionType) {
          try {
            const response = await getRecommendationGuide(actionType);
            setShowActionDetails(prev => ({
              ...prev,
              [title]: {
                ...response,
                expanded: !prev[title]?.expanded
              }
            }));
          } catch (error) {
            console.error('Failed to load guide:', error);
            Alert.alert('Error', 'Failed to load guide. Please try again.');
          }
        } else {
          setShowActionDetails(prev => ({
            ...prev,
            [title]: { expanded: !prev[title]?.expanded }
          }));
        }
      }
    };

    const details = showActionDetails[title];

    return (
      <View style={[styles.card, { marginBottom: 16 }]}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
          <Text style={[styles.label, { flex: 1, marginBottom: 0 }]}>{title}</Text>
          {automated && <Icon name="flash-on" size={16} color={colors.yellow400} />}
        </View>
        
        <Text style={[styles.description, { textAlign: 'left', marginBottom: 12 }]}>{description}</Text>
        
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <View style={{ flexDirection: 'row', gap: 12 }}>
            <View style={[
              styles.badge,
              impact === 'high' ? styles.badgeHigh : impact === 'medium' ? styles.badgeMedium : styles.badgeLow
            ]}>
              <Text style={[
                styles.badgeText,
                impact === 'high' ? styles.badgeTextHigh : impact === 'medium' ? styles.badgeTextMedium : styles.badgeTextLow
              ]}>
                {impact} impact
              </Text>
            </View>
            
            <View style={[
              styles.badge,
              effort === 'low' ? styles.badgeHigh : effort === 'medium' ? styles.badgeMedium : styles.badgeLow
            ]}>
              <Text style={[
                styles.badgeText,
                effort === 'low' ? styles.badgeTextHigh : effort === 'medium' ? styles.badgeTextMedium : styles.badgeTextLow
              ]}>
                {effort} effort
              </Text>
            </View>
          </View>
          
          <TouchableOpacity
            onPress={handleActionClick}
            style={{ flexDirection: 'row', alignItems: 'center' }}
          >
            <Text style={{ color: colors.blue400, fontSize: 14, fontWeight: '500' }}>
              {automated ? 'Auto-fix' : 'Get guide'}
            </Text>
            <Icon name="arrow-forward" size={12} color={colors.blue400} style={{ marginLeft: 4 }} />
          </TouchableOpacity>
        </View>

        {details?.expanded && (
          <View style={{ marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: colors.gray700 }}>
            {details.steps && (
              <View style={{ marginBottom: 12 }}>
                <Text style={[styles.label, { marginBottom: 8 }]}>Step-by-step guide:</Text>
                {details.steps.map((step, index) => (
                  <View key={index} style={{ flexDirection: 'row', marginBottom: 4 }}>
                    <Text style={{ color: colors.blue400, fontSize: 12, marginRight: 8 }}>{index + 1}.</Text>
                    <Text style={{ color: colors.gray400, fontSize: 12, flex: 1 }}>{step}</Text>
                  </View>
                ))}
              </View>
            )}
            
            {details.tools && (
              <View style={{ marginBottom: 12 }}>
                <Text style={[styles.label, { marginBottom: 8 }]}>Available tools:</Text>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                  {details.tools.map((tool, index) => (
                    <View key={index} style={{ backgroundColor: colors.gray700, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 }}>
                      <Text style={{ color: colors.gray300, fontSize: 12 }}>{tool}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            {details.estimatedTime && (
              <Text style={{ color: colors.gray400, fontSize: 12, marginBottom: 4 }}>
                <Text style={{ fontWeight: '600' }}>Time needed:</Text> {details.estimatedTime}
              </Text>
            )}
            
            {details.impact && (
              <Text style={{ color: colors.gray400, fontSize: 12 }}>
                <Text style={{ fontWeight: '600' }}>Why it matters:</Text> {details.impact}
              </Text>
            )}
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue500} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={[styles.card, { marginBottom: 24 }]}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View style={{ flex: 1 }}>
              <Text style={styles.sectionTitle}>AI Reputation Report</Text>
              <Text style={styles.description}>
                for {analysisData.person.name} in {analysisData.person.location}
              </Text>
            </View>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={{ color: colors.blue400, fontSize: 16, fontWeight: '500' }}>← New Scan</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Reputation Scores */}
        <View style={styles.card}>
          <Text style={[styles.sectionTitle, { marginBottom: 24 }]}>Your AI Reputation Score</Text>
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

          {/* Enhancement Opportunity Alert */}
          <View style={styles.alert}>
            <Icon name="warning" size={20} color={colors.yellow400} style={styles.alertIcon} />
            <View style={styles.alertContent}>
              <Text style={styles.alertTitle}>Enhancement Opportunity</Text>
              <Text style={styles.alertDescription}>
                Your visibility score shows room for growth. AI assistants are finding limited recent information about you.
              </Text>
            </View>
          </View>
        </View>

        {/* Two Column Layout for larger content */}
        <View style={{ marginBottom: 24 }}>
          {/* AI Search Patterns */}
          <View style={[styles.card, { marginBottom: 16 }]}>
            <Text style={styles.sectionTitle}>AI Search Patterns</Text>
            <Text style={[styles.description, { marginBottom: 24 }]}>
              How different AI assistants search for information about you:
            </Text>
            
            {Object.entries(analysisData.searchQueries).map(([platform, data]) => (
              <SearchQuery 
                key={platform}
                platform={platform.charAt(0).toUpperCase() + platform.slice(1)}
                confidence={data.confidence}
                scope={data.scope}
              />
            ))}
          </View>

          {/* What AI Finds */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>What AI Finds</Text>
            <View style={{ marginTop: 16 }}>
              {analysisData.findings.map((finding, index) => (
                <View key={index} style={{
                  borderLeftWidth: 4,
                  borderLeftColor: finding.status === 'found' || finding.status === 'strong' ? colors.green500 :
                    finding.status === 'moderate' || finding.status === 'limited' ? colors.yellow500 : colors.red400,
                  paddingLeft: 16,
                  marginBottom: 16
                }}>
                  <Text style={[styles.label, { marginBottom: 4 }]}>{finding.category}</Text>
                  <Text style={[styles.description, { textAlign: 'left' }]}>{finding.description}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>

        {/* Recommendations */}
        <View style={styles.card}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <Text style={styles.sectionTitle}>Personalized Enhancement Plan</Text>
            <Text style={[styles.description, { fontSize: 12 }]}>Ranked by impact</Text>
          </View>

          {analysisData.recommendations.map((rec, index) => (
            <ActionItem
              key={index}
              title={rec.title}
              description={rec.description}
              impact={rec.impact}
              effort={rec.effort}
              automated={rec.automated}
              actionType={rec.actionType}
            />
          ))}

          {/* Pro Upgrade Section */}
          <View style={{
            marginTop: 24,
            padding: 24,
            backgroundColor: colors.gray700,
            borderRadius: 12,
            borderWidth: 1,
            borderColor: colors.gray600
          }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.label, { fontSize: 18, marginBottom: 4 }]}>
                  Ready to enhance your AI reputation?
                </Text>
                <Text style={styles.description}>
                  Get detailed guides and automated tools with RepEnhance Pro
                </Text>
              </View>
              <TouchableOpacity style={[styles.primaryButton, { marginLeft: 16 }]}>
                <Text style={styles.buttonText}>Upgrade to Pro</Text>
                <Icon name="arrow-forward" size={16} color={colors.white} style={{ marginLeft: 8 }} />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default ResultsScreen;
