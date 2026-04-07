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
      // 1. Start Job — 60s timeout for upload + initial processing
      const res = await axios.post(`${API_BASE}/api/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000
      });

      if (!res.data.success) {
        throw new Error(res.data.error || "Failed to start analysis.");
      }

      const jobId = res.data.data.job_id;
      if (!jobId) throw new Error("No Job ID returned from server.");

      // 2. Poll Status
      let retryCount = 0;
      const MAX_RETRIES = 30; // 30 retries gives ~90s of breathing room

      const poll = async () => {
        try {
          const statusRes = await axios.get(`${API_BASE}/api/status/${jobId}`, {
            timeout: 15000
          });

          // 404 means job not found — server likely restarted (Render free tier spin-up)
          if (statusRes.status === 404 || !statusRes.data.success) {
            throw new Error(statusRes.data?.error || "Job not found on server.");
          }

          retryCount = 0; // reset on successful response
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
          // If the server explicitly said the job doesn't exist, stop immediately
          if (pollErr.response?.status === 404) {
            setError("Analysis session expired. The server may have restarted — please re-upload your file.");
            setIsLoading(false);
            return;
          }

          retryCount += 1;
          if (retryCount >= MAX_RETRIES) {
            setError("Connection lost after multiple retries. Please check your network and try again.");
            setIsLoading(false);
            return;
          }
          // Exponential backoff: 2s, 3s, 4s, ... capped at 8s
          const delay = Math.min(2000 + (retryCount - 1) * 500, 8000);
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
