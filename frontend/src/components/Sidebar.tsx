import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Sliders,
  Mic,
  History,
  Settings,
  HelpCircle,
} from 'lucide-react';

interface SidebarProps {
  activeSessionId?: string | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeSessionId }) => {
  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/documents', label: 'Documents & Ingest', icon: FileText },
    { to: '/configure', label: 'Configuration', icon: Sliders },
    ...(activeSessionId
      ? [{ to: `/interview/${activeSessionId}`, label: 'Live Interview', icon: Mic, badge: 'Active' }]
      : []),
    { to: '/history', label: 'Interview History', icon: History },
    { to: '/settings', label: 'Settings & Status', icon: Settings },
  ];

  return (
    <aside className="w-64 flex-shrink-0 hidden md:block bg-white dark:bg-navy-850 border-r border-slate-200 dark:border-navy-700 min-h-[calc(100vh-4rem)]">
      <div className="p-4 flex flex-col justify-between h-full">
        <div className="space-y-1">
          <p className="px-3 text-[11px] font-bold text-slate-400 dark:text-slate-400 uppercase tracking-wider mb-2">
            Navigation
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-50 dark:bg-navy-800 text-indigo-600 dark:text-indigo-400 font-bold border-l-2 border-indigo-600 dark:border-indigo-400 shadow-xs'
                      : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-navy-800'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 animate-pulse border border-emerald-300 dark:border-emerald-700/60">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>

        {/* Quick Help Card */}
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800/80 border border-slate-200 dark:border-navy-700">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white mb-1">
            <HelpCircle className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span>RAG Mock Workflow</span>
          </div>
          <p className="text-[11px] text-slate-600 dark:text-[#CBD5E1] leading-relaxed">
            Upload your resume & job requirements to generate tailored interview questions and receive instant AI feedback.
          </p>
        </div>
      </div>
    </aside>
  );
};
