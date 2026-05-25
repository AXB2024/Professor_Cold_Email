import axios from "axios";

const baseURL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const client = axios.create({
  baseURL,
  timeout: 60000,
});

const parseError = (error) => {
  if (error?.response?.data?.detail) {
    return typeof error.response.data.detail === "string"
      ? error.response.data.detail
      : JSON.stringify(error.response.data.detail);
  }
  if (error?.response?.data?.error) return error.response.data.error;
  return error?.message || "Something went wrong. Please try again.";
};

const wrap = async (request) => {
  try {
    const response = await request;
    return response.data;
  } catch (error) {
    throw new Error(parseError(error));
  }
};

export const parseResume = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return wrap(
    client.post("/parse_resume", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    })
  );
};

export const generateEmails = async (payload) => wrap(client.post("/generate_emails", payload));

export const reviewEmail = async (payload) => wrap(client.post("/review_email", payload));

export const sendEmail = async (payload) => wrap(client.post("/send_email", payload));

export const getAnalytics = async () => wrap(client.get("/analytics"));

export const updateAnalyticsStatus = async (payload) =>
  wrap(client.post("/analytics/update_status", payload));

