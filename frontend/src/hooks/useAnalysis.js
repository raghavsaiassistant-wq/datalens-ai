import { useState } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://datalens-ai.onrender.com';

export const useAnalysis = () => {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [progress, setProgress] = useState(0); // 1-6
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const uploadFile = async (file) => {
    setIsLoading(true);
    setError(null);
    setProgress(1);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // 1. Start Job
      const res = await axios.post(`${API_BASE}/api/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      
      if (!res.data.success) {
        throw new Error(res.data.error || "Failed to start analysis.");
      }

      const jobId = res.data.data.job_id;
      if (!jobId) throw new Error("No Job ID returned from server.");

      // 2. Poll Status
      const poll = async () => {
        try {
          const statusRes = await axios.get(`${API_BASE}/api/status/${jobId}`);
          
          if (!statusRes.data.success) {
            throw new Error(statusRes.data.error || "Failed to fetch status.");
          }

          const { status, progress: step, message, result } = statusRes.data.data;
          const jobErr = statusRes.data.error;

          setProgress(step);
          setLoadingStep(message);

          if (status === "completed") {
            setAnalysisResult(result.data);
            setSessionId(result.session_id);
            setIsLoading(false);
          } else if (status === "failed") {
            setError(jobErr || "Analysis failed on the server.");
            setIsLoading(false);
          } else {
            // Continue polling
            setTimeout(poll, 800);
          }
        } catch (pollErr) {
          setError(pollErr.message || "Connection lost. Retrying...");
          setTimeout(poll, 2000);
        }
      };

      poll();

    } catch (err) {
      const msg = err.response?.data?.error || err.message || "An unexpected error occurred.";
      setError(msg);
      setIsLoading(false);
    }
  };

  const askQuestion = async (question) => {
    if (!sessionId) throw new Error("No active session");
    const res = await axios.post(`${API_BASE}/api/ask`, { question, session_id: sessionId });
    if (!res.data.success) throw new Error(res.data.error || "Failed to get answer");
    return res.data.data.answer;
  };

  const resetAnalysis = () => {
    setAnalysisResult(null);
    setSessionId(null);
    setError(null);
  };

  return { uploadFile, askQuestion, resetAnalysis, analysisResult, isLoading, loadingStep, progress, error, sessionId };
};
