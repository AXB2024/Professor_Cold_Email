import React from "react";
import StatusBadge from "./StatusBadge";

const metricCards = [
  { key: "total_generated", label: "Total Generated" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
  { key: "sent", label: "Sent" },
  { key: "responses", label: "Responses" },
  { key: "response_rate", label: "Response Rate" },
];

const AnalyticsDashboard = ({ analytics, onUpdateStatus, statusUpdating }) => {
  const rows = analytics?.records || [];
  return (
    <section className="space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {metricCards.map((metric) => (
          <div key={metric.key} className="rounded-2xl bg-white p-4 shadow-soft ring-1 ring-slate-200">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{metric.label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">
              {metric.key === "response_rate"
                ? `${analytics?.response_rate ?? 0}%`
                : analytics?.[metric.key] ?? 0}
            </p>
          </div>
        ))}
      </div>

      <div className="rounded-2xl bg-white p-5 shadow-soft ring-1 ring-slate-200">
        <h3 className="mb-3 text-base font-semibold text-slate-900">Outreach Tracking</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="py-2 pr-4">Professor</th>
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Score</th>
                <th className="py-2 pr-4">Last Updated</th>
                <th className="py-2 pr-4">Response</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td className="py-4 text-slate-500" colSpan={6}>
                    No records yet.
                  </td>
                </tr>
              ) : (
                rows.map((record) => (
                  <tr key={record.draft_id} className="border-b border-slate-100">
                    <td className="py-3 pr-4 font-medium text-slate-900">{record.professor_name}</td>
                    <td className="py-3 pr-4 text-slate-600">{record.professor_email}</td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={record.status} />
                    </td>
                    <td className="py-3 pr-4 text-slate-700">{record.score}</td>
                    <td className="py-3 pr-4 text-slate-500">
                      {new Date(record.last_updated).toLocaleString()}
                    </td>
                    <td className="py-3 pr-4">
                      <select
                        value={record.response_status || "no_response"}
                        onChange={(event) => onUpdateStatus(record.draft_id, event.target.value)}
                        disabled={statusUpdating === record.draft_id}
                        className="rounded-lg border border-slate-300 px-2 py-1 text-xs text-slate-700"
                      >
                        <option value="no_response">No Response</option>
                        <option value="responded">Responded</option>
                        <option value="follow_up_needed">Follow Up Needed</option>
                      </select>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};

export default AnalyticsDashboard;

