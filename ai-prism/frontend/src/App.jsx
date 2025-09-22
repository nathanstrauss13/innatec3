import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, Target, Award, CheckCircle, ArrowRight, Sparkles, Building2, FileText, Lock, Zap, Eye, ChevronRight, X, Loader2 } from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';

const App = () => {
  const [currentView, setCurrentView] = useState('landing');
  const [brandName, setBrandName] = useState('');
  const [email, setEmail] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisId, setAnalysisId] = useState(null);

  const handleStartAnalysis = async () => {
    if (brandName.trim() && email.trim()) {
      setIsAnalyzing(true);
      try {
        const response = await axios.post(`${API_URL}/analyze/preview`, {
          brandName,
          email
        });
        
        setAnalysisId(response.data.analysisId);
        
        // Poll for results
        const pollInterval = setInterval(async () => {
          const statusResponse = await axios.get(`${API_URL}/analyze/status/${response.data.analysisId}`);
          
          if (statusResponse.data.status === 'completed') {
            clearInterval(pollInterval);
            setAnalysisData(statusResponse.data.preview);
            setIsAnalyzing(false);
            setCurrentView('preview');
          } else if (statusResponse.data.status === 'failed') {
            clearInterval(pollInterval);
            setIsAnalyzing(false);
            alert('Analysis failed. Please try again.');
          }
        }, 2000);
        
      } catch (error) {
        console.error('Analysis error:', error);
        setIsAnalyzing(false);
        alert('Failed to start analysis. Please try again.');
      }
    }
  };

  const handleUnlockReport = async () => {
    // In production, integrate Stripe here
    setCurrentView('payment');
  };

  if (currentView === 'landing') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
        {/* Navigation */}
        <nav className="px-8 py-6 flex justify-between items-center border-b border-blue-900/20">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white">AI PRism</span>
          </div>
          <button 
            onClick={() => setCurrentView('analysis')}
            className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105"
          >
            Get Started
          </button>
        </nav>

        {/* Hero Section */}
        <div className="px-8 py-20 max-w-6xl mx-auto">
          <div className="text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-900/30 backdrop-blur-sm rounded-full border border-blue-800/50">
              <Zap className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-blue-300">AI-Powered PR Intelligence</span>
            </div>
            
            <h1 className="text-6xl font-bold text-white leading-tight">
              See How Your Brand<br />
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Shows Up in AI
              </span>
            </h1>
            
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Discover which publishers influence your AI search visibility and get actionable insights to enhance your brand's AI presence
            </p>

            <div className="flex gap-4 justify-center pt-4">
              <button 
                onClick={() => setCurrentView('analysis')}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-xl shadow-blue-900/50"
              >
                Analyze Your Brand
                <ArrowRight className="inline ml-2 w-5 h-5" />
              </button>
              <button className="px-8 py-4 bg-white/10 backdrop-blur-sm text-white rounded-xl font-semibold text-lg hover:bg-white/20 transition-all border border-white/20">
                View Sample Report
              </button>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 mt-24">
            <div className="p-6 bg-gradient-to-br from-blue-900/20 to-purple-900/20 backdrop-blur-sm rounded-2xl border border-blue-800/30 hover:border-blue-700/50 transition-all">
              <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center mb-4">
                <Search className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Multi-AI Analysis</h3>
              <p className="text-gray-400">Query ChatGPT, Claude, Perplexity, and Google AI to see comprehensive visibility</p>
            </div>
            
            <div className="p-6 bg-gradient-to-br from-blue-900/20 to-purple-900/20 backdrop-blur-sm rounded-2xl border border-blue-800/30 hover:border-blue-700/50 transition-all">
              <div className="w-12 h-12 bg-purple-600/20 rounded-xl flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Publisher Insights</h3>
              <p className="text-gray-400">Identify which media outlets influence your AI visibility most</p>
            </div>
            
            <div className="p-6 bg-gradient-to-br from-blue-900/20 to-purple-900/20 backdrop-blur-sm rounded-2xl border border-blue-800/30 hover:border-blue-700/50 transition-all">
              <div className="w-12 h-12 bg-green-600/20 rounded-xl flex items-center justify-center mb-4">
                <TrendingUp className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Competitive Edge</h3>
              <p className="text-gray-400">See how you stack up against competitors in AI responses</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'analysis') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
        <nav className="px-8 py-6 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white">AI PRism</span>
          </div>
          <button 
            onClick={() => setCurrentView('landing')}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </nav>

        <div className="px-8 py-16 max-w-2xl mx-auto">
          <div className="text-center space-y-4 mb-12">
            <h2 className="text-4xl font-bold text-white">
              Analyze Your Brand's AI Visibility
            </h2>
            <p className="text-gray-300">
              Enter your company name to see how you appear across AI platforms
            </p>
          </div>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Company Name
              </label>
              <input
                type="text"
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                placeholder="e.g., Salesforce, Nike, Microsoft"
                className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-blue-800/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-600 focus:bg-white/15 transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email (for report delivery)
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-blue-800/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-600 focus:bg-white/15 transition-all"
              />
            </div>

            <button
              onClick={handleStartAnalysis}
              disabled={!brandName.trim() || !email.trim() || isAnalyzing}
              className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-[1.02] shadow-xl shadow-blue-900/50"
            >
              {isAnalyzing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing across AI platforms...
                </span>
              ) : (
                'Start Free Analysis'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'preview' && analysisData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
        <nav className="px-8 py-6 flex justify-between items-center border-b border-blue-900/20">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white">AI PRism</span>
          </div>
        </nav>

        <div className="px-8 py-12 max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-900/30 backdrop-blur-sm rounded-full border border-green-800/50 mb-4">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-300">Analysis Complete</span>
            </div>
            <h1 className="text-4xl font-bold text-white mb-2">
              {brandName} AI Visibility Report
            </h1>
            <p className="text-gray-300">Preview Results</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="p-6 bg-gradient-to-br from-blue-900/20 to-purple-900/20 backdrop-blur-sm rounded-2xl border border-blue-800/30">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-gray-400 text-sm mb-1">AI Visibility Score</p>
                  <p className="text-4xl font-bold text-white">{analysisData.visibilityScore}</p>
                </div>
                <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
                  <Award className="w-6 h-6 text-blue-400" />
                </div>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                  style={{ width: `${analysisData.visibilityScore}%` }}
                />
              </div>
            </div>

            <div className="p-6 bg-gradient-to-br from-green-900/20 to-blue-900/20 backdrop-blur-sm rounded-2xl border border-green-800/30">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-gray-400 text-sm mb-1">vs. Competitors</p>
                  <p className="text-4xl font-bold text-green-400">{analysisData.competitorComparison}</p>
                  <p className="text-sm text-gray-400 mt-2">Better visibility</p>
                </div>
                <div className="w-12 h-12 bg-green-600/20 rounded-xl flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-green-400" />
                </div>
              </div>
            </div>
          </div>

          <div className="p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 mb-8">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Eye className="w-5 h-5 text-purple-400" />
              Top Publishers Influencing Your AI Visibility
            </h3>
            <div className="space-y-3">
              {analysisData.topPublishers.map((publisher, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <span className="text-white font-medium">{publisher.name}</span>
                  <span className="text-gray-400 text-sm">{publisher.citations} citations</span>
                </div>
              ))}
              <div className="p-3 bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-lg border border-blue-700/50">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300 flex items-center gap-2">
                    <Lock className="w-4 h-4" />
                    12 more publishers in full report
                  </span>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </div>
          </div>

          <div className="text-center p-8 bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-sm rounded-2xl border border-blue-800/50">
            <h3 className="text-2xl font-bold text-white mb-2">Unlock Full Report</h3>
            <p className="text-gray-300 mb-6">Get complete analysis with all publishers, queries, and strategic recommendations</p>
            <button
              onClick={handleUnlockReport}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-xl shadow-blue-900/50"
            >
              Get Full Report - $99
              <ArrowRight className="inline ml-2 w-5 h-5" />
            </button>
            <p className="text-sm text-gray-400 mt-4">
              <FileText className="inline w-4 h-4 mr-1" />
              Delivered as premium PDF report
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'payment') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
        <nav className="px-8 py-6 flex justify-between items-center border-b border-blue-900/20">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white">AI PRism</span>
          </div>
        </nav>

        <div className="px-8 py-16 max-w-lg mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">Complete Your Purchase</h2>
            <p className="text-gray-300">Unlock the full {brandName} AI Visibility Report</p>
          </div>

          <div className="p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 mb-6">
            <div className="flex justify-between items-center mb-4">
              <span className="text-white font-semibold">AI Visibility Report</span>
              <span className="text-2xl font-bold text-white">$99</span>
            </div>
            <div className="space-y-2 text-sm text-gray-300">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>Complete publisher analysis</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>All query performance data</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>Competitor comparison</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>Strategic PR recommendations</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <input
              type="text"
              placeholder="Card number"
              className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-blue-800/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-600"
            />
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="MM/YY"
                className="px-4 py-3 bg-white/10 backdrop-blur-sm border border-blue-800/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-600"
              />
              <input
                type="text"
                placeholder="CVC"
                className="px-4 py-3 bg-white/10 backdrop-blur-sm border border-blue-800/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-600"
              />
            </div>
            <button className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all">
              Complete Purchase
            </button>
          </div>

          <p className="text-center text-sm text-gray-400 mt-6">
            Secure payment processed by Stripe
          </p>
        </div>
      </div>
    );
  }

  return null;
};

export default App;
