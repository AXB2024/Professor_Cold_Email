import React from "react";

const styles = {
  draft: "bg-slate-100 text-slate-700 border-slate-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-rose-50 text-rose-700 border-rose-200",
  sent: "bg-blue-50 text-blue-700 border-blue-200",
  responded: "bg-violet-50 text-violet-700 border-violet-200",
  no_response: "bg-amber-50 text-amber-700 border-amber-200",
  follow_up_needed: "bg-orange-50 text-orange-700 border-orange-200",
};

const labels = {
  draft: "Draft",
  approved: "Approved",
  rejected: "Rejected",
  sent: "Sent",
  responded: "Responded",
  no_response: "No Response",
  follow_up_needed: "Follow Up Needed",
};

const StatusBadge = ({ status }) => {
  const normalized = status || "draft";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${
        styles[normalized] || styles.draft
      }`}
    >
      {labels[normalized] || normalized}
    </span>
  );
};

export default StatusBadge;

