import React, { useEffect, useMemo, useState } from "react";
import {
  generateEmails,
  getAnalytics,
  reviewEmail,
  sendEmail,
  updateAnalyticsStatus,
} from "../api/api";
import AnalyticsDashboard from "./AnalyticsDashboard.jsx";
import EmailCard from "./EmailCard.jsx";
import ProfessorForm, { makeProfessor } from "./ProfessorForm.jsx";
import ResumeUpload from "./ResumeUpload.jsx";
import StudentProfileCard from "./StudentProfileCard.jsx";

const initialStudent = {
  name: "",
  university: "",
  major: "",
  skills: "",
  interests: "",
};

const parseCsv = (value) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const toDisplayStatus = (status, responseStatus) => {
  if (responseStatus && responseStatus !== "no_response") return responseStatus;
  if (status === "pending_review") return "draft";
  return status || "draft";
};

const Dashboard = () => {
  const [student, setStudent] = useState(initialStudent);
  const [professors, setProfessors] = useState([makeProfessor()]);
  const [emails, setEmails] = useState([]);
  const [analytics, setAnalytics] = useState({
    total_generated: 0,
    approved: 0,
    rejected: 0,
    sent: 0,
    responses: 0,
    response_rate: 0,
    records: [],
  });
  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [extractedFromResume, setExtractedFromResume] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const analyticsByDraft = useMemo(() => {
    const map = {};
    for (const record of analytics.records || []) {
      map[record.draft_id] = record;
    }
    return map;
  }, [analytics.records]);

  const refreshAnalytics = async () => {
    try {
      const data = await getAnalytics();
      setAnalytics(data);
    } catch {
      // keep UI usable even if analytics fetch fails
    }
  };

  useEffect(() => {
    refreshAnalytics();
  }, []);

  const validateBeforeGenerate = () => {
    if (!student.name.trim() || !student.university.trim() || !student.major.trim()) {
      return "Please complete Name, University, and Major in Student Profile.";
    }
    const badProfessor = professors.find((professor) => {
      const hasResearch = professor.research_text.trim() || professor.website_url.trim();
      return !professor.name.trim() || !professor.email.trim() || !hasResearch;
    });
    if (badProfessor) {
      return "Each professor needs Name, Email, and either Website URL or Research Text.";
    }
    return "";
  };

  const buildGeneratePayload = () => ({
    student: {
      name: student.name.trim(),
      university: student.university.trim(),
      major: student.major.trim(),
      skills: parseCsv(student.skills),
      interests: parseCsv(student.interests),
    },
    professors: professors.map((professor) => {
      const payload = {
        name: professor.name.trim(),
        email: professor.email.trim(),
      };
      if (professor.website_url.trim()) payload.website_url = professor.website_url.trim();
      if (professor.research_text.trim()) payload.research_text = professor.research_text.trim();
      return payload;
    }),
  });

  const updateEmailItem = (draftId, patch) => {
    setEmails((prev) => prev.map((email) => (email.draft_id === draftId ? { ...email, ...patch } : email)));
  };

  const setActionLoading = (draftId, actionKey, loading) => {
    setEmails((prev) =>
      prev.map((email) =>
        email.draft_id === draftId
          ? { ...email, loading: { ...email.loading, [actionKey]: loading } }
          : email
      )
    );
  };

  const onResumeParsed = (parsed) => {
    setStudent((prev) => ({
      ...prev,
      name: parsed.name || prev.name,
      university: parsed.university || prev.university,
      major: parsed.major || prev.major,
      skills: parsed.skills?.length ? parsed.skills.join(", ") : prev.skills,
    }));
    setExtractedFromResume(true);
  };

  const onGenerateEmails = async () => {
    setError("");
    setSuccess("");
    const formError = validateBeforeGenerate();
    if (formError) {
      setError(formError);
      return;
    }

    setLoadingGenerate(true);
    try {
      const payload = buildGeneratePayload();
      const response = await generateEmails(payload);
      const items = (response.items || []).map((item) => ({
        ...item,
        editedEmail: item.email || "",
        message: item.error || "",
        messageType: item.error ? "error" : "",
        loading: { approve: false, edit: false, reject: false, send: false },
        displayStatus: toDisplayStatus(item.status, "no_response"),
      }));
      setEmails(items);
      setSuccess(`Generated ${items.length} email draft${items.length === 1 ? "" : "s"}.`);
      await refreshAnalytics();
    } catch (apiError) {
      setError(apiError.message || "Failed to generate emails.");
    } finally {
      setLoadingGenerate(false);
    }
  };

  const onApprove = async (draftId) => {
    setActionLoading(draftId, "approve", true);
    try {
      const response = await reviewEmail({ draft_id: draftId, action: "approve" });
      const analyticsRecord = analyticsByDraft[draftId];
      updateEmailItem(draftId, {
        status: response.status,
        score: response.score,
        editedEmail: response.email,
        displayStatus: toDisplayStatus(response.status, analyticsRecord?.response_status),
        message: "Approved.",
        messageType: "success",
      });
      await refreshAnalytics();
    } catch (apiError) {
      updateEmailItem(draftId, { message: apiError.message || "Failed to approve.", messageType: "error" });
    } finally {
      setActionLoading(draftId, "approve", false);
    }
  };

  const onSaveEdit = async (draftId) => {
    const current = emails.find((item) => item.draft_id === draftId);
    if (!current?.editedEmail?.trim()) {
      updateEmailItem(draftId, { message: "Email body cannot be empty.", messageType: "error" });
      return;
    }
    setActionLoading(draftId, "edit", true);
    try {
      const response = await reviewEmail({
        draft_id: draftId,
        action: "edit",
        edited_email: current.editedEmail,
      });
      const feedback = response.feedback?.length ? ` ${response.feedback.join(" ")}` : "";
      const analyticsRecord = analyticsByDraft[draftId];
      updateEmailItem(draftId, {
        status: response.status,
        score: response.score,
        editedEmail: response.email,
        displayStatus: toDisplayStatus(response.status, analyticsRecord?.response_status),
        message: `Edit saved.${feedback}`,
        messageType: "success",
      });
      await refreshAnalytics();
    } catch (apiError) {
      updateEmailItem(draftId, { message: apiError.message || "Failed to save edit.", messageType: "error" });
    } finally {
      setActionLoading(draftId, "edit", false);
    }
  };

  const onReject = async (draftId) => {
    setActionLoading(draftId, "reject", true);
    try {
      const response = await reviewEmail({ draft_id: draftId, action: "reject" });
      updateEmailItem(draftId, {
        status: response.status,
        displayStatus: "rejected",
        message: "Rejected.",
        messageType: "success",
      });
      await refreshAnalytics();
    } catch (apiError) {
      updateEmailItem(draftId, { message: apiError.message || "Failed to reject.", messageType: "error" });
    } finally {
      setActionLoading(draftId, "reject", false);
    }
  };

  const onSend = async (draftId) => {
    setActionLoading(draftId, "send", true);
    try {
      await sendEmail({ draft_id: draftId, provider: "smtp" });
      const analyticsRecord = analyticsByDraft[draftId];
      updateEmailItem(draftId, {
        status: "sent",
        displayStatus: toDisplayStatus("sent", analyticsRecord?.response_status),
        message: "Email sent successfully.",
        messageType: "success",
      });
      await refreshAnalytics();
    } catch (apiError) {
      updateEmailItem(draftId, { message: apiError.message || "Failed to send email.", messageType: "error" });
    } finally {
      setActionLoading(draftId, "send", false);
    }
  };

  const onUpdateResponseStatus = async (draftId, status) => {
    setStatusUpdating(draftId);

    const optimisticRecords = (analytics.records || []).map((record) =>
      record.draft_id === draftId ? { ...record, response_status: status, status } : record
    );
    setAnalytics((prev) => ({ ...prev, records: optimisticRecords }));

    try {
      await updateAnalyticsStatus({ draft_id: draftId, status });
      setEmails((prev) =>
        prev.map((item) =>
          item.draft_id === draftId ? { ...item, displayStatus: toDisplayStatus(item.status, status) } : item
        )
      );
      await refreshAnalytics();
    } catch {
      // If endpoint fails, keep local optimistic state as requested.
    } finally {
      setStatusUpdating("");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto flex max-w-[1500px]">
        <aside className="sticky top-0 hidden h-screen w-64 flex-col border-r border-slate-200 bg-white p-6 lg:flex">
          <h1 className="mb-8 text-xl font-bold text-slate-900">Outreach OS</h1>
          <nav className="space-y-3 text-sm font-medium">
            {["Dashboard", "Student Profile", "Professors", "Draft Emails", "Analytics"].map((item) => (
              <span
                key={item}
                className="block rounded-xl px-3 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
              >
                {item}
              </span>
            ))}
          </nav>
        </aside>

        <main className="w-full p-4 md:p-8">
          <header className="mb-6 flex flex-col gap-4 rounded-2xl bg-white p-6 shadow-soft ring-1 ring-slate-200 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">Startup Dashboard</p>
              <h2 className="text-2xl font-bold text-slate-900">Professor Outreach Automation</h2>
              <p className="text-sm text-slate-500">Generate, review, send, and track personalized research emails.</p>
            </div>
            <button
              type="button"
              onClick={onGenerateEmails}
              disabled={loadingGenerate}
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {loadingGenerate ? "Generating..." : "Generate Emails"}
            </button>
          </header>

          {error ? (
            <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
          ) : null}
          {success ? (
            <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {success}
            </div>
          ) : null}

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <ResumeUpload onResumeParsed={onResumeParsed} setError={setError} setSuccess={setSuccess} />
            <StudentProfileCard
              student={student}
              onChange={setStudent}
              extractedFromResume={extractedFromResume}
            />
          </div>

          <div className="mt-4">
            <ProfessorForm professors={professors} setProfessors={setProfessors} />
          </div>

          <section className="mt-6 space-y-4">
            <h3 className="text-lg font-semibold text-slate-900">Draft Emails</h3>
            {emails.length === 0 ? (
              <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow-soft ring-1 ring-slate-200">
                No email drafts yet. Add profile and professors, then click Generate Emails.
              </div>
            ) : (
              emails.map((item) => {
                const analyticsRecord = analyticsByDraft[item.draft_id];
                return (
                  <EmailCard
                    key={item.draft_id || item.professor_email}
                    item={{
                      ...item,
                      displayStatus: toDisplayStatus(item.status, analyticsRecord?.response_status),
                    }}
                    onChange={(draftId, value) => updateEmailItem(draftId, { editedEmail: value })}
                    onApprove={onApprove}
                    onSaveEdit={onSaveEdit}
                    onReject={onReject}
                    onSend={onSend}
                  />
                );
              })
            )}
          </section>

          <section className="mt-6">
            <AnalyticsDashboard
              analytics={analytics}
              onUpdateStatus={onUpdateResponseStatus}
              statusUpdating={statusUpdating}
            />
          </section>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
