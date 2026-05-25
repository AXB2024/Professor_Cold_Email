import React from "react";

const StudentProfileCard = ({ student, onChange, extractedFromResume }) => {
  const updateField = (field, value) => {
    onChange((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <div className="rounded-2xl bg-white p-5 shadow-soft ring-1 ring-slate-200">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Student Profile</h2>
          <p className="text-sm text-slate-500">Review and edit before generating emails.</p>
        </div>
        {extractedFromResume ? (
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
            Extracted from resume
          </span>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <label className="space-y-1">
          <span className="text-sm font-medium text-slate-700">Name</span>
          <input
            value={student.name}
            onChange={(e) => updateField("name", e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
            placeholder="Alex Kim"
          />
        </label>
        <label className="space-y-1">
          <span className="text-sm font-medium text-slate-700">University</span>
          <input
            value={student.university}
            onChange={(e) => updateField("university", e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
            placeholder="State University"
          />
        </label>
        <label className="space-y-1 md:col-span-2">
          <span className="text-sm font-medium text-slate-700">Major</span>
          <input
            value={student.major}
            onChange={(e) => updateField("major", e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
            placeholder="Computer Science"
          />
        </label>
        <label className="space-y-1 md:col-span-2">
          <span className="text-sm font-medium text-slate-700">Skills (comma-separated)</span>
          <input
            value={student.skills}
            onChange={(e) => updateField("skills", e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
            placeholder="Python, FastAPI, SQL, PyTorch"
          />
        </label>
        <label className="space-y-1 md:col-span-2">
          <span className="text-sm font-medium text-slate-700">Interests (manual entry)</span>
          <input
            value={student.interests}
            onChange={(e) => updateField("interests", e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
            placeholder="NLP, Systems, AI for Healthcare"
          />
        </label>
      </div>
    </div>
  );
};

export default StudentProfileCard;

