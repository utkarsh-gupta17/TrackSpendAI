import React from 'react';
import { TrendingDown, TrendingUp, HandCoins, Activity } from 'lucide-react';

const CATEGORY_COLORS = {
  'Food & Dining': '#f97316',
  'Transport': '#3b82f6',
  'Recharge & Bills': '#10b981',
  'Shopping': '#7c3aed',
  'Entertainment': '#ec4899',
  'Healthcare': '#ef4444',
  'Education': '#f59e0b',
  'Transfers': '#64748b',
  'Investment': '#06b6d4',
  'Insurance': '#059669',
  'Other': '#94a3b8'
};

const StatCard = ({ title, value, icon: Icon, color }) => (
  <div className="bg-card border border-border p-6 rounded-3xl shadow-xl">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-3 rounded-2xl ${color} bg-opacity-10`}>
        <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
      </div>
    </div>
    <h3 className="text-gray-400 text-sm mb-1">{title}</h3>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

export default function SpendingDashboard({ report }) {
  if (!report) return null;
  
  const { 
    health_score = 0, 
    health_label = 'N/A', 
    savings_rate = 0, 
    metadata = { total_debit: 0, total_credit: 0 }, 
    transactions = [] 
  } = report;

  const categories = React.useMemo(() => {
    return Object.entries(report.by_category || {}).sort((a, b) => {
      try {
          return (b[1]?.total || 0) - (a[1]?.total || 0);
      } catch(e) { return 0; }
    });
  }, [report.by_category]);

  const months = React.useMemo(() => {
    return Object.entries(report.by_month || {}).sort((a,b) => {
      try {
          const dateA = new Date(a[0]);
          const dateB = new Date(b[0]);
          if (isNaN(dateA) || isNaN(dateB)) return 0;
          return dateA - dateB;
      } catch(e) { return 0; }
    });
  }, [report.by_month]);

  const [trendCategory, setTrendCategory] = React.useState('All');
  const [trendYear, setTrendYear] = React.useState('All');

  const years = React.useMemo(() => {
    return ['All', ...new Set(transactions.map(t => {
      if (!t.date) return null;
      const d = new Date(t.date);
      return isNaN(d) ? null : d.getFullYear().toString();
    }).filter(Boolean))].sort();
  }, [transactions]);

  const filteredMonths = React.useMemo(() => {
    const trendMap = {};
    (transactions || []).forEach(tx => {
      if (!tx.date) return;
      const date = new Date(tx.date);
      if (isNaN(date)) return;
      
      const y = date.getFullYear().toString();
      const m = date.toLocaleString('default', { month: 'short' });
      const monthStr = `${m} ${y}`;
      
      const type = tx.type || '';
      const matchesCategory = trendCategory === 'All' || tx.category === trendCategory;
      const matchesYear = trendYear === 'All' || y === trendYear;
      
      if (matchesCategory && matchesYear) {
         if (!trendMap[monthStr]) trendMap[monthStr] = { debit: 0, dateObj: date };
         if (type.toLowerCase() === 'debit') {
            trendMap[monthStr].debit += Number(tx.amount) || 0;
         }
      }
    });

    return Object.entries(trendMap)
      .filter(([_, data]) => data.debit > 0)
      .sort((a,b) => a[1].dateObj - b[1].dateObj)
      .map(([label, data]) => [label, data]);
  }, [transactions, trendCategory, trendYear]);

  return (
    <div className="space-y-8">
      {/* Summary Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Spent" 
          value={`₹${metadata.total_debit.toLocaleString('en-IN')}`}
          icon={TrendingDown}
          color="bg-red-500"
        />
        <StatCard 
          title="Total Received" 
          value={`₹${metadata.total_credit.toLocaleString('en-IN')}`}
          icon={TrendingUp}
          color="bg-green-500"
        />
        <StatCard 
          title="Savings Rate" 
          value={`${savings_rate}%`}
          icon={HandCoins}
          color={savings_rate > 20 ? "bg-green-500" : savings_rate > 10 ? "bg-amber-500" : "bg-red-500"}
        />
        <div className="bg-card border border-border p-6 rounded-3xl shadow-xl flex flex-col justify-center items-center text-center">
          <div className="relative w-20 h-20 flex items-center justify-center mb-2">
            <svg className="w-full h-full -rotate-90">
              <circle cx="40" cy="40" r="36" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              <circle 
                cx="40" cy="40" r="36" fill="transparent" 
                stroke="#7c3aed" strokeWidth="8" 
                strokeDasharray="226.2"
                strokeDashoffset={226.2 * (1 - health_score / 100)}
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <span className="absolute text-xl font-bold">{health_score}</span>
          </div>
          <p className="text-xs font-bold uppercase tracking-widest text-accent mb-1">Health Score</p>
          <span className={`text-sm px-3 py-1 rounded-full bg-opacity-10 font-bold ${
            health_label === 'Excellent' ? 'text-green-500 bg-green-500' :
            health_label === 'Good' ? 'text-blue-500 bg-blue-500' :
            health_label === 'Fair' ? 'text-amber-500 bg-amber-500' : 'text-red-500 bg-red-500'
          }`}>
            {health_label}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Category Breakdown */}
        <div className="bg-card border border-border p-8 rounded-3xl shadow-xl">
          <h3 className="text-xl font-bold mb-8">Spending by Category</h3>
          <div className="space-y-6">
            {categories.map(([name, data]) => (
              <div key={name}>
                <div className="flex justify-between text-sm mb-2">
                  <span className="font-medium">{name}</span>
                  <span className="text-gray-400">₹{data.total.toLocaleString('en-IN')} ({data.percentage_of_spend.toFixed(1)}%)</span>
                </div>
                <div className="h-2 w-full bg-border rounded-full overflow-hidden">
                  <div 
                    className="h-full transition-all duration-1000 ease-out"
                    style={{ 
                      width: `${data.percentage_of_spend}%`,
                      backgroundColor: CATEGORY_COLORS[name] || '#94a3b8'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Trend */}
        <div className="bg-card border border-border p-8 rounded-3xl shadow-xl overflow-hidden flex flex-col h-[400px]">
          <div className="flex justify-between items-center mb-6 shrink-0">
            <h3 className="text-xl font-bold">Monthly Trend</h3>
            <div className="flex gap-4">
              <select 
                value={trendCategory}
                onChange={(e) => setTrendCategory(e.target.value)}
                className="bg-border/30 border border-border rounded-xl px-4 py-2 text-xs font-bold outline-none focus:border-accent"
              >
                <option value="All">All Categories</option>
                {Object.keys(report.by_category || {}).sort().map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
              <select 
                value={trendYear}
                onChange={(e) => setTrendYear(e.target.value)}
                className="bg-border/30 border border-border rounded-xl px-4 py-2 text-xs font-bold outline-none focus:border-accent"
              >
                {years.map(y => (
                  <option key={y} value={y}>{y === 'All' ? 'All Years' : y}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex-grow overflow-y-auto pr-4 space-y-5 scrollbar-hide">
             {filteredMonths.map(([month, data], i) => {
                const maxDebit = Math.max(...filteredMonths.map(m => m[1].debit), 1);
                const width = (data.debit / maxDebit) * 100;
                
                return (
                  <div key={month} className="flex items-center gap-4 group relative">
                    <span className="w-16 text-[10px] font-medium text-subtle whitespace-nowrap text-right shrink-0">{month}</span>
                    <div className="flex-grow relative flex items-center h-8 cursor-pointer">
                        {/* Spend Bar */}
                        <div 
                           className="h-4/5 bg-accent rounded-r-xl transition-all duration-1000 ease-out group-hover:bg-purple-400 z-10 shadow-sm"
                           style={{ width: `${width}%` }}
                        />
                    </div>
                    {/* Custom Tooltip */}
                    <div className="absolute left-[80px] top-full mt-1 opacity-0 group-hover:opacity-100 transition-opacity bg-tooltip border border-tooltip-border text-foreground px-4 py-3 rounded-xl whitespace-nowrap z-50 pointer-events-none shadow-2xl flex flex-col items-start min-w-[140px] space-y-1">
                        <div className="flex justify-between w-full text-xs gap-4">
                          <span className="text-muted-foreground">Spend:</span>
                          <span className="font-bold text-accent">₹{data.debit.toLocaleString('en-IN')}</span>
                        </div>
                        {data.debit === maxDebit && maxDebit > 0 && <span className="text-subtle mt-2 uppercase tracking-widest text-[9px] pt-1 border-t border-tooltip-border w-full text-center">Highest Spend</span>}
                    </div>
                  </div>
                )
             })}
          </div>
        </div>
      </div>
    </div>
  );
}
