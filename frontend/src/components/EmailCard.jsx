import React from "react";
import StatusBadge from "./StatusBadge.jsx";

const EmailCard = ({
  item,
  onChange,
  onApprove,
  onSaveEdit,
  onReject,
  onSend,
}) => {
  const canSend = item.status === "approved" && !item.loading.send;

  return (
    <div className="rounded-2xl bg-white p-5 shadow-soft ring-1 ring-slate-200">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">{item.professor_name}</h3>
          <p className="text-sm text-slate-500">{item.professor_email}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={item.displayStatus} />
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              item.score >= 7 ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
            }`}
          >
            Score {item.score}
          </span>
        </div>
      </div>

      <div className="mb-3">
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Research Summary
        </label>
        <p className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">{item.summary}</p>
      </div>

      <div className="mb-4">
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Email Draft</label>
        <textarea
          value={item.editedEmail}
          onChange={(e) => onChange(item.draft_id, e.target.value)}
          rows={8}
          className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 transition focus:ring-2"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onApprove(item.draft_id)}
          disabled={item.loading.approve || item.status === "approved" || item.status === "sent"}
          className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {item.loading.approve ? "Approving..." : "Approve"}
        </button>
        <button
          type="button"
          onClick={() => onSaveEdit(item.draft_id)}
          disabled={item.loading.edit}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {item.loading.edit ? "Saving..." : "Save Edit"}
        </button>
        <button
          type="button"
          onClick={() => onReject(item.draft_id)}
          disabled={item.loading.reject || item.status === "sent"}
          className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100 disabled:opacity-50"
        >
          {item.loading.reject ? "Rejecting..." : "Reject"}
        </button>
        <button
          type="button"
          onClick={() => onSend(item.draft_id)}
          disabled={!canSend || item.status === "sent"}
          className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {item.loading.send ? "Sending..." : item.status === "sent" ? "Sent" : "Send"}
        </button>
      </div>

      {item.message ? (
        <p
          className={`mt-3 text-sm ${
            item.messageType === "error"
              ? "text-rose-600"
              : item.messageType === "success"
                ? "text-emerald-700"
                : "text-slate-600"
          }`}
        >
          {item.message}
        </p>
      ) : null}
    </div>
  );
};

export default EmailCard;
