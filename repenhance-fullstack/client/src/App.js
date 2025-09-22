import React, { useState } from 'react';
import axios from 'axios';
import { Search, User, MapPin, GraduationCap, CheckCircle, AlertCircle, Zap, Shield, Star, ArrowRight, Sparkles } from 'lucide-react';
import './App.css';

const App = () => {
  const [currentStep, setCurrentStep] = useState('input');
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    affiliation: ''
  });
  const [isScanning, setIsScanning] = useState(false);
  const [showActionDetails, setShowActionDetails] = useState({});
  const [analysisData, setAnalysisData] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleScan = async () => {
    setIsScanning(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/analyze-reputation', formData);
      setAnalysisData(response.data);
      setTimeout(() => {
        setIsScanning(false);
        setCurrentStep('results');
      }, 2000); // Show loading for a bit even if API is fast
    } catch (error) {
      console.error('Analysis failed:', error);
      setError(error.response?.data?.message || 'Analysis failed. Please try again.');
      setIsScanning(false);
    }
  };

  const SearchQuery = ({ platform, confidence, scope }) => (
    <div className="bg-gray-800 border border-gray-700 p-4 rounded-lg mb-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-200">{platform}</span>
        <span className={`text-xs px-2 py-1 rounded-full ${confidence === 'high' ? 'bg-green-900 text-green-300 border border-green-700' : confidence === 'medium' ? 'bg-yellow-900 text-yellow-300 border border-yellow-700' : 'bg-red-900 text-red-300 border border-red-700'}`}>
          {confidence} match likelihood
        </span>
      </div>
      <div className="text-xs text-gray-400">
        {scope}
      </div>
    </div>
  );

  const ReputationScore = ({ score, category }) => (
    <div className="text-center">
      <div className={`text-3xl font-bold ${score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
        {score}
      </div>
      <div className="text-xs text-gray-400 uppercase tracking-wide">{category}</div>
    </div>
  );

  const ActionItem = ({ title, description, impact, effort, automated = false, actionType }) => {
    const handleActionClick = async () => {
      if (automated) {
        alert(`Auto-fix initiated for: ${title}\nThis would automatically optimize your profile settings.`);
      } else {
        if (actionType) {
          try {
            const response = await axios.get(`/api/recommendations/${actionType}`);
            setShowActionDetails(prev => ({
              ...prev,
              [title]: {
                ...response.data,
                expanded: !prev[title]?.expanded
              }
            }));
          } catch (error) {
            console.error('Failed to load guide:', error);
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
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:bg-gray-750 transition-all">
        <div className="flex items-start justify-between mb-2">
          <h4 className="font-medium text-gray-100">{title}</h4>
          {automated && <Zap className="w-4 h-4 text-yellow-400" />}
        </div>
        <p className="text-sm text-gray-300 mb-3">{description}</p>
        <div className="flex items-center justify-between">
          <div className="flex space-x-3 text-xs">
            <span className={`px-2 py-1 rounded-full ${impact === 'high' ? 'bg-green-900 text-green-300 border border-green-700' : impact === 'medium' ? 'bg-yellow-900 text-yellow-300 border border-yellow-700' : 'bg-blue-900 text-blue-300 border border-blue-700'}`}>
              {impact} impact
            </span>
            <span className={`px-2 py-1 rounded-full ${effort === 'low' ? 'bg-green-900 text-green-300 border border-green-700' : effort === 'medium' ? 'bg-yellow-900 text-yellow-300 border border-yellow-700' : 'bg-red-900 text-red-300 border border-red-700'}`}>
              {effort} effort
            </span>
          </div>
          <button 
            onClick={handleActionClick}
            className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center"
          >
            {automated ? 'Auto-fix' : 'Get guide'} 
            <ArrowRight className="w-3 h-3 ml-1" />
          </button>
        </div>
        
        {details?.expanded && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="space-y-3">
              {details.steps && (
                <div>
                  <h5 className="text-sm font-medium text-gray-200 mb-2">Step-by-step guide:</h5>
                  <ol className="text-xs text-gray-400 space-y-1">
                    {details.steps.map((step, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-blue-400 mr-2">{index + 1}.</span>
                        {step}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
              {details.tools && (
                <div>
                  <h5 className="text-sm font-medium text-gray-200 mb-2">Available tools:</h5>
                  <div className="flex flex-wrap gap-2">
                    {details.tools.map((tool, index) => (
                      <span key={index} className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {details.estimatedTime && (
                <div className="text-xs text-gray-400">
                  <strong>Time needed:</strong> {details.estimatedTime}
                </div>
              )}
              {details.impact && (
                <div className="text-xs text-gray-400">
                  <strong>Why it matters:</strong> {details.impact}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (currentStep === 'input') {
    return (
      <div className="min-h-screen bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-blue-400 mr-2" />
              <h1 className="text-3xl font-bold text-white">RepEnhance</h1>
            </div>
            <p className="text-xl text-gray-300 mb-2">Boost your AI reputation</p>
            <p className="text-gray-400 max-w-2xl mx-auto">
              See what ChatGPT, Claude, and Gemini find when people search for you. 
              Get actionable insights to enhance your digital presence.
            </p>
          </div>

          <div className="max-w-2xl mx-auto">
            <div className="bg-gray-800 border border-gray-700 rounded-2xl shadow-2xl p-8">
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-blue-900 border border-blue-700 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="w-8 h-8 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Discover your AI footprint</h2>
                <p className="text-gray-400">We'll check what AI assistants find about you across the web</p>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="flex items-center text-sm font-medium text-gray-200 mb-2">
                    <User className="w-4 h-4 mr-2" />
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="e.g. Sarah Johnson"
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors placeholder-gray-400"
                  />
                </div>

                <div>
                  <label className="flex items-center text-sm font-medium text-gray-200 mb-2">
                    <MapPin className="w-4 h-4 mr-2" />
                    Location
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    placeholder="e.g. New York, NY"
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors placeholder-gray-400"
                  />
                </div>

                <div>
                  <label className="flex items-center text-sm font-medium text-gray-200 mb-2">
                    <GraduationCap className="w-4 h-4 mr-2" />
                    Recent Affiliation
                  </label>
                  <input
                    type="text"
                    value={formData.affiliation}
                    onChange={(e) => handleInputChange('affiliation', e.target.value)}
                    placeholder="e.g. Stanford University, Google, etc."
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors placeholder-gray-400"
                  />
                </div>

                {error && (
                  <div className="p-4 bg-red-900 border border-red-700 rounded-lg">
                    <p className="text-red-300 text-sm">{error}</p>
                  </div>
                )}

                <button
                  onClick={handleScan}
                  disabled={!formData.name || !formData.location || isScanning}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
                >
                  <Search className="w-5 h-5 mr-2" />
                  {isScanning ? 'Analyzing...' : 'Enhance My AI Reputation'}
                </button>
              </div>

              <div className="mt-8 pt-6 border-t border-gray-700">
                <div className="flex items-center justify-center space-x-8 text-sm text-gray-400">
                  <div className="flex items-center">
                    <Shield className="w-4 h-4 mr-1" />
                    Private & Secure
                  </div>
                  <div className="flex items-center">
                    <Zap className="w-4 h-4 mr-1" />
                    Instant Results
                  </div>
                  <div className="flex items-center">
                    <Star className="w-4 h-4 mr-1" />
                    AI-Powered
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isScanning) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 border-4 border-gray-700 border-t-blue-500 rounded-full animate-spin mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-white mb-2">Analyzing your AI presence...</h2>
          <p className="text-gray-400 mb-4">Checking ChatGPT, Claude, Gemini, and search engines</p>
          <div className="max-w-md mx-auto space-y-2">
            <div className="flex items-center justify-between bg-gray-800 border border-gray-700 p-3 rounded-lg">
              <span className="text-sm text-gray-300">Generating search queries...</span>
              <CheckCircle className="w-4 h-4 text-green-400" />
            </div>
            <div className="flex items-center justify-between bg-gray-800 border border-gray-700 p-3 rounded-lg">
              <span className="text-sm text-gray-300">Analyzing AI responses...</span>
              <div className="w-4 h-4 border-2 border-gray-600 border-t-blue-500 rounded-full animate-spin"></div>
            </div>
            <div className="flex items-center justify-between bg-gray-800 border border-gray-700 p-3 rounded-lg opacity-50">
              <span className="text-sm text-gray-400">Generating recommendations...</span>
              <div className="w-4 h-4 border-2 border-gray-700 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-white">No analysis data available</p>
          <button 
            onClick={() => setCurrentStep('input')}
            className="mt-4 text-blue-400 hover:text-blue-300"
          >
            Start New Analysis
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-sm p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">AI Reputation Report</h1>
              <p className="text-gray-400">for {analysisData.person.name} in {analysisData.person.location}</p>
            </div>
            <button 
              onClick={() => setCurrentStep('input')}
              className="text-blue-400 hover:text-blue-300 font-medium"
            >
              ← New Scan
            </button>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-6">Your AI Reputation Score</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <ReputationScore score={analysisData.scores.overall} category="Overall" />
            <ReputationScore score={analysisData.scores.professional} category="Professional" />
            <ReputationScore score={analysisData.scores.visibility} category="Visibility" />
            <ReputationScore score={analysisData.scores.accuracy} category="Accuracy" />
          </div>
          <div className="mt-6 p-4 bg-yellow-900 border border-yellow-700 rounded-lg">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-yellow-400 mr-2 mt-0.5" />
              <div>
                <h3 className="font-medium text-yellow-300">Enhancement Opportunity</h3>
                <p className="text-sm text-yellow-200 mt-1">
                  Your visibility score shows room for growth. AI assistants are finding limited recent information about you.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-white mb-4">AI Search Patterns</h2>
            <p className="text-gray-400 mb-6">How different AI assistants search for information about you:</p>
            
            {Object.entries(analysisData.searchQueries).map(([platform, data]) => (
              <SearchQuery 
                key={platform}
                platform={platform.charAt(0).toUpperCase() + platform.slice(1)}
                confidence={data.confidence}
                scope={data.scope}
              />
            ))}
          </div>

          <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-bold text-white mb-4">What AI Finds</h2>
            <div className="space-y-4">
              {analysisData.findings.map((finding, index) => (
                <div key={index} className={`border-l-4 pl-4 ${
                  finding.status === 'found' || finding.status === 'strong' ? 'border-green-500' :
                  finding.status === 'moderate' || finding.status === 'limited' ? 'border-yellow-500' :
                  'border-red-500'
                }`}>
                  <h3 className="font-medium text-gray-100">{finding.category}</h3>
                  <p className="text-sm text-gray-400">{finding.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-sm p-6 mt-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">Personalized Enhancement Plan</h2>
            <span className="text-sm text-gray-400">Ranked by impact</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
          </div>

          <div className="mt-8 p-6 bg-gradient-to-r from-gray-700 to-gray-600 border border-gray-600 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">Ready to enhance your AI reputation?</h3>
                <p className="text-gray-300">Get detailed guides and automated tools with RepEnhance Pro</p>
              </div>
              <button className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center">
                Upgrade to Pro
                <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
