import React, { useState } from 'react';
import { Search, Download, ChevronLeft, ChevronRight, Filter } from 'lucide-react';

export default function TransactionTable({ transactions = [] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [monthFilter, setMonthFilter] = useState('All');
  const [yearFilter, setYearFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const categories = ['All', ...new Set(transactions.map(t => t.category))].sort();

  const years = ['All', ...new Set(transactions.map(t => {
    if (!t.date) return null;
    const d = new Date(t.date);
    return isNaN(d) ? null : d.getFullYear().toString();
  }).filter(Boolean))].sort();

  const validMonths = new Set(transactions.map(t => {
    if (!t.date) return null;
    const d = new Date(t.date);
    return isNaN(d) ? null : d.toLocaleString('default', { month: 'short' });
  }).filter(Boolean));

  const allMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const months = ['All', ...allMonths.filter(m => validMonths.has(m))];

  const filtered = transactions.filter(t => {
    const desc = (t.description || '').toLowerCase();
    const cp = (t.counterparty || '').toLowerCase();
    const search = searchTerm.toLowerCase();
    const matchesSearch = desc.includes(search) || cp.includes(search);
    const matchesCategory = categoryFilter === 'All' || t.category === categoryFilter;

    const date = new Date(t.date);
    const m = date.toLocaleString('default', { month: 'short' });
    const y = date.getFullYear().toString();

    const matchesMonth = monthFilter === 'All' || m === monthFilter;
    const matchesYear = yearFilter === 'All' || y === yearFilter;
    const matchesType = typeFilter === 'All' || (t.type || '').toLowerCase() === typeFilter.toLowerCase();

    return matchesSearch && matchesCategory && matchesMonth && matchesYear && matchesType;
  });

  const totalPages = Math.ceil(filtered.length / rowsPerPage);
  const currentRows = filtered.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

  const exportCSV = () => {
    const headers = ['Date', 'Description', 'Category', 'Amount', 'Type'];
    const rows = filtered.map(t => [
      new Date(t.date).toLocaleDateString(),
      t.description,
      t.category,
      t.amount,
      t.type
    ]);

    const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "TrackSpendAI_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-card border border-border rounded-3xl overflow-hidden mt-12 shadow-xl">
      <div className="p-8 border-b border-border flex flex-col md:flex-row gap-4 justify-between items-center">
        <h3 className="text-xl font-bold">Transactions</h3>
        <div className="flex flex-wrap gap-4 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-background border border-border rounded-xl pl-12 pr-4 py-2.5 text-sm focus:outline-none focus:border-accent"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-background border border-border rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-accent"
          >
            {categories.map(c => <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>)}
          </select>
          <select
            value={monthFilter}
            onChange={(e) => setMonthFilter(e.target.value)}
            className="bg-background border border-border rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-accent"
          >
            {months.map(m => <option key={m} value={m}>{m === 'All' ? 'All Months' : m}</option>)}
          </select>
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value)}
            className="bg-background border border-border rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-accent"
          >
            {years.map(y => <option key={y} value={y}>{y === 'All' ? 'All Years' : y}</option>)}
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-background border border-border rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-accent"
          >
            <option value="All">All Types</option>
            <option value="debit">Spend (Debit)</option>
            <option value="credit">Earn (Credit)</option>
          </select>
          <button
            onClick={exportCSV}
            className="bg-accent/10 hover:bg-accent/20 text-accent px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all"
          >
            <Download className="w-4 h-4" /> Export
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-background/50 text-gray-500 text-[11px] uppercase tracking-widest border-b border-border">
              <th className="px-8 py-4 font-bold">Date</th>
              <th className="px-8 py-4 font-bold">Transaction Detail</th>
              <th className="px-8 py-4 font-bold">Category</th>
              <th className="px-8 py-4 font-bold text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {currentRows.map((t, i) => (
              <tr key={i} className="hover:bg-accent/5 transition-colors group">
                <td className="px-8 py-5 text-sm text-gray-400">{new Date(t.date).toLocaleDateString()}</td>
                <td className="px-8 py-5">
                  <p className="font-medium text-sm group-hover:text-white transition-colors">{t.counterparty || t.description}</p>
                  {t.counterparty && <p className="text-[10px] text-gray-600 truncate max-w-[300px] mt-0.5">{t.description}</p>}
                </td>
                <td className="px-8 py-5">
                  <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-accent/10 text-accent border border-accent/20">
                    {t.category}
                  </span>
                </td>
                <td className={`px-8 py-5 text-sm font-bold text-right ${t.type === 'debit' ? 'text-red-400' : 'text-green-400'}`}>
                  {t.type === 'debit' ? '-' : '+'}₹{(t.amount || 0).toLocaleString('en-IN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="p-8 border-t border-border flex justify-between items-center bg-background/30">
        <p className="text-xs text-gray-500">
          Showing {Math.min(filtered.length, (currentPage - 1) * rowsPerPage + 1)}-{Math.min(filtered.length, currentPage * rowsPerPage)} of {filtered.length} transactions
        </p>
        <div className="flex gap-2">
          <button
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(p => p - 1)}
            className="p-2 border border-border rounded-lg disabled:opacity-30 hover:bg-card transition-all"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(p => p + 1)}
            className="p-2 border border-border rounded-lg disabled:opacity-30 hover:bg-card transition-all"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
