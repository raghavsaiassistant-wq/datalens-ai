import { useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const STEPS = [
  "📂 Reading your file...",
  "🔍 Profiling data structure...",
  "🤖 Running AI analysis...",
  "📊 Building your dashboard...",
  "✨ Almost ready..."
];

export const useAnalysis = () => {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const uploadFile = async (file) => {
    setIsLoading(true);
    setError(null);
    setLoadingStep(STEPS[0]);

    // Simulate progress steps since backend is a single call
    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep = (currentStep + 1) % STEPS.length;
      if (currentStep < STEPS.length - 1) setLoadingStep(STEPS[currentStep]);
    }, 3000);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_BASE}/api/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      clearInterval(interval);
      setLoadingStep(STEPS[4]);
      
      if (res.data.status === "success") {
        setAnalysisResult(res.data.data);
        setSessionId(res.data.session_id);
      } else {
        setError("Analysis failed: " + res.data.message);
      }
    } catch (err) {
      clearInterval(interval);
      setError(err.response?.data?.error || err.message || "An unexpected error occurred.");
    } finally {
      clearInterval(interval);
      setIsLoading(false);
    }
  };

  const askQuestion = async (question) => {
    if (!sessionId) throw new Error("No active session");
    const res = await axios.post(`${API_BASE}/api/ask`, { question, session_id: sessionId });
    if (res.data.status !== "success") throw new Error(res.data.error || "Failed to get answer");
    return res.data.answer;
  };

  const resetAnalysis = () => {
    setAnalysisResult(null);
    setSessionId(null);
    setError(null);
  };

  return { uploadFile, askQuestion, resetAnalysis, analysisResult, isLoading, loadingStep, error, sessionId };
};
