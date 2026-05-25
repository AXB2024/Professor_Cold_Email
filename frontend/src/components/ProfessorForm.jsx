import React from "react";

const makeProfessor = () => ({
  id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  name: "",
  email: "",
  website_url: "",
  research_text: "",
});

const ProfessorForm = ({ professors, setProfessors }) => {
  const update = (id, field, value) => {
    setProfessors((prev) =>
      prev.map((professor) => (professor.id === id ? { ...professor, [field]: value } : professor))
    );
  };

  const addProfessor = () => setProfessors((prev) => [...prev, makeProfessor()]);
  const removeProfessor = (id) =>
    setProfessors((prev) => (prev.length > 1 ? prev.filter((prof) => prof.id !== id) : prev));

  return (
    <div className="rounded-2xl bg-white p-5 shadow-soft ring-1 ring-slate-200">
      <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Professors</h2>
          <p className="text-sm text-slate-500">Website URL or Research Text is required for each professor.</p>
        </div>
        <button
          type="button"
          onClick={addProfessor}
          className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
        >
          Add Professor
        </button>
      </div>

      <div className="space-y-4">
        {professors.map((professor, index) => (
          <div key={professor.id} className="rounded-xl border border-slate-200 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-800">Professor {index + 1}</h3>
              <button
                type="button"
                onClick={() => removeProfessor(professor.id)}
                disabled={professors.length === 1}
                className="rounded-lg px-2 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:opacity-50"
              >
                Remove
              </button>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <input
                value={professor.name}
                onChange={(e) => update(professor.id, "name", e.target.value)}
                placeholder="Professor name"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
              />
              <input
                value={professor.email}
                onChange={(e) => update(professor.id, "email", e.target.value)}
                placeholder="professor@university.edu"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
              />
              <input
                value={professor.website_url}
                onChange={(e) => update(professor.id, "website_url", e.target.value)}
                placeholder="Website URL"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2 md:col-span-2"
              />
              <textarea
                value={professor.research_text}
                onChange={(e) => update(professor.id, "research_text", e.target.value)}
                placeholder="Research text"
                rows={4}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2 md:col-span-2"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export { makeProfessor };
export default ProfessorForm;

