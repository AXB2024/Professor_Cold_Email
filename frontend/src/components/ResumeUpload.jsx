import React, { useRef } from "react";
import { parseResume } from "../api/api";

const acceptedTypes = ".pdf,.docx,.txt";

const ResumeUpload = ({ onResumeParsed, setError, setSuccess }) => {
  const fileRef = useRef(null);
  const [loading, setLoading] = React.useState(false);

  const onUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const parsed = await parseResume(file);
      onResumeParsed(parsed);
      setSuccess("Resume parsed successfully. Profile fields were auto-filled.");
    } catch (error) {
      setError(error.message || "Resume parsing failed. Please fill profile manually.");
    } finally {
      setLoading(false);
      if (fileRef.current) {
        fileRef.current.value = "";
      }
    }
  };

  return (
    <div className="rounded-2xl bg-white p-5 shadow-soft ring-1 ring-slate-200">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Resume Upload</h2>
          <p className="text-sm text-slate-500">
            Upload PDF, DOCX, or TXT to auto-fill student profile fields.
          </p>
        </div>
        <label className="inline-flex cursor-pointer items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
          {loading ? "Parsing..." : "Upload Resume"}
          <input
            ref={fileRef}
            type="file"
            className="hidden"
            accept={acceptedTypes}
            onChange={onUpload}
            disabled={loading}
          />
        </label>
      </div>
      {loading ? (
        <div className="mt-4 flex items-center gap-2 text-sm text-slate-500">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
          Extracting profile from resume...
        </div>
      ) : null}
    </div>
  );
};

export default ResumeUpload;

