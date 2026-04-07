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
  const [uploadStartTime, setUploadStartTime] = useState(null);

  const uploadFile = async (file) => {
    setIsLoading(true);
    setError(null);
    setProgress(1);
    setUploadStartTime(Date.now());

    const formData = new FormData();
    formData.append("file", file);

    try {
      // 1. Start Job — 180s timeout covers cold start + upload
      const res = await axios.post(`${API_BASE}/api/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 180000
      });

      if (!res.data.success) {
        throw new Error(res.data.error || "Failed to start analysis.");
      }

      const jobId = res.data.data.job_id;
      if (!jobId) throw new Error("No Job ID returned from server.");

      // 2. Poll Status
      let retryCount = 0;
      let coldStartCount = 0;
      const MAX_RETRIES = 30;
      const MAX_COLD_START = 5; // 5 × 3s = 15s grace window for Render cold start

      const poll = async () => {
        try {
          const statusRes = await axios.get(`${API_BASE}/api/status/${jobId}`, {
            timeout: 15000
          });

          if (!statusRes.data.success) {
            throw new Error(statusRes.data?.error || "Job not found on server.");
          }

          retryCount = 0;
          coldStartCount = 0;
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
            setTimeout(poll, 800);
          }
        } catch (pollErr) {
          // Flask returned 404 explicitly — job doesn't exist on this server instance
          if (pollErr.response?.status === 404) {
            setError("Analysis session expired. The server may have restarted — please re-upload your file.");
            setIsLoading(false);
            return;
          }

          // No response at all = network error / server still spinning up (cold start)
          if (!pollErr.response && coldStartCount < MAX_COLD_START) {
            coldStartCount += 1;
            setLoadingStep("⚡ Starting AI engine...");
            setTimeout(poll, 3000);
            return;
          }

          retryCount += 1;
          if (retryCount >= MAX_RETRIES) {
            setError("Analysis is taking longer than expected. The server may be starting up. Please try again.");
            setIsLoading(false);
            return;
          }
          // Backoff: 3s, 3.5s, 4s, ... capped at 8s
          const delay = Math.min(3000 + (retryCount - 1) * 500, 8000);
          setLoadingStep(`Connection interrupted. Retrying (${retryCount}/${MAX_RETRIES})...`);
          setTimeout(poll, delay);
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
    setIsLoading(false);
    setLoadingStep("");
    setProgress(0);
    setUploadStartTime(null);
  };

  return { uploadFile, askQuestion, resetAnalysis, analysisResult, isLoading, loadingStep, progress, error, sessionId, uploadStartTime };
};
