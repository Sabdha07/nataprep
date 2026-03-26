import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
});

// Attach JWT token to all requests
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        if (refresh) {
          const res = await axios.post(`${BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refresh,
          });
          const newToken = res.data.access_token;
          localStorage.setItem("access_token", newToken);
          original.headers.Authorization = `Bearer ${newToken}`;
          return api(original);
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// API functions
export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
};

export const practiceApi = {
  createSession: (mode: string, config?: Record<string, unknown>) =>
    api.post("/practice/sessions", { mode, config }),
  listSessions: () => api.get("/practice/sessions"),
  getNextQuestion: (sessionId?: string) =>
    api.get("/practice/next-question", { params: { session_id: sessionId } }),
  submitAnswer: (
    sessionId: string,
    data: {
      question_id: string;
      selected_option_id: string;
      time_taken_seconds: number;
      confidence_level?: number;
    }
  ) => api.post(`/practice/sessions/${sessionId}/submit`, data),
  endSession: (sessionId: string) =>
    api.post(`/practice/sessions/${sessionId}/end`),
};

export const drawingApi = {
  listTasks: (params?: Record<string, unknown>) =>
    api.get("/drawing/tasks", { params }),
  getNextTask: () => api.get("/drawing/tasks/next"),
  submitDrawing: (formData: FormData) =>
    api.post("/drawing/submit", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  listSubmissions: () => api.get("/drawing/submissions"),
  getEvaluation: (submissionId: string) =>
    api.get(`/drawing/submissions/${submissionId}/evaluation`),
};

export const analyticsApi = {
  getDashboard: () => api.get("/analytics/dashboard"),
  getWeakAreas: () => api.get("/analytics/weak-areas"),
  getPredictions: () => api.get("/analytics/predictions"),
  getProgress: (days?: number) =>
    api.get("/analytics/progress", { params: { days } }),
};

export const conceptsApi = {
  list: (category?: string) =>
    api.get("/concepts", { params: { category } }),
  getMastery: (conceptId: string) =>
    api.get(`/concepts/${conceptId}/mastery`),
};
