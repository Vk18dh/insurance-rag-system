"use client"

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  ShieldCheck, 
  FileText, 
  Settings, 
  Menu, 
  X, 
  LogOut,
  Activity
} from 'lucide-react';
import { useAuth } from '@/components/auth-provider';

interface ManagementLayoutProps {
  children: React.ReactNode;
  role: string | null;
}

export function ManagementLayout({ children, role }: ManagementLayoutProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const pathname = usePathname();
  const { logout, user } = useAuth();

  const getNavItems = () => {
    const items = [];
    
    if (role === 'admin') {
      items.push({ name: 'Dashboard', href: '/admin', icon: LayoutDashboard });
      items.push({ name: 'Security Audit', href: '/admin/audit', icon: ShieldCheck });
      items.push({ name: 'RAG Evaluation', href: '/admin/evaluation', icon: Activity });
      items.push({ name: 'Documents', href: '/admin/documents', icon: FileText });
    }
    
    if (role === 'expert') {
      items.push({ name: 'Review Queue', href: '/expert', icon: ShieldCheck });
    }

    return items;
  };

  const navItems = getNavItems();

  const SidebarContent = () => (
    <div className="flex h-full flex-col bg-[#050A12] text-slate-300 border-r border-slate-800/60">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-cyan-500/10 flex items-center justify-center text-cyan-400 font-bold border border-cyan-500/20">
          IL
        </div>
        <div>
          <span className="text-lg font-bold text-white tracking-tight">InsuraLens</span>
          <span className="text-[10px] block text-cyan-500 font-medium uppercase tracking-wider">Management Console</span>
        </div>
      </div>
      
      <nav className="flex-1 space-y-1 px-4 py-4">
        <div className="mb-4 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Modules
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setIsMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                isActive 
                  ? 'bg-cyan-500/10 text-cyan-400' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800/60">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 text-xs font-medium border border-slate-700">
            {user?.username?.substring(0, 2).toUpperCase() || 'AD'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-200 truncate">{user?.username || 'User'}</p>
            <p className="text-xs text-slate-500 truncate capitalize">{role}</p>
          </div>
          <button 
            onClick={logout} 
            className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#07111F] overflow-hidden text-slate-200 font-sans">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 flex-shrink-0 relative z-20">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsMobileOpen(false)} />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-[#050A12] shadow-2xl">
            <button
              onClick={() => setIsMobileOpen(false)}
              className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white bg-slate-800/50 rounded-md"
            >
              <X className="h-5 w-5" />
            </button>
            <SidebarContent />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10 overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden h-16 flex items-center justify-between px-4 border-b border-slate-800/60 bg-[#050A12]">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-xs font-bold border border-cyan-500/20">
              IL
            </div>
            <span className="font-bold text-white tracking-tight">InsuraLens</span>
          </div>
          <button
            onClick={() => setIsMobileOpen(true)}
            className="p-2 -mr-2 text-slate-400 hover:text-white"
          >
            <Menu className="h-6 w-6" />
          </button>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-[#07111F]">
          <div className="mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
