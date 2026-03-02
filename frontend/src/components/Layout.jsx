import React from 'react';
import { Activity, Brain, Settings, AlertCircle, Menu } from 'lucide-react';

const Layout = ({ children, status }) => {
    return (
        <div className="flex h-screen w-screen bg-medical-bg text-medical-text">
            {/* Sidebar Removed as per user request to maximize visualization area */}

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden relative">
                <header className="h-16 bg-white border-b border-medical-surface flex items-center justify-between px-6 shadow-sm z-10">
                    <div className="flex items-center gap-4">
                        <h1 className="text-lg font-semibold text-slate-700">Computational Neuroscience Platform</h1>
                        <span className="px-2 py-1 bg-blue-50 text-blue-600 text-xs font-mono rounded border border-blue-100">v1.2.0</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 border border-green-200 rounded-full text-xs font-bold">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            SYSTEM ONLINE
                        </div>
                    </div>
                </header>
                {children}
            </main>
        </div>
    );
};

const NavItem = ({ icon: Icon, label, active }) => (
    <button className={`flex items-center gap-4 p-3 rounded-lg transition-all w-full text-left ${active ? 'bg-blue-50 text-blue-700 font-semibold' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}>
        <Icon className="w-5 h-5" />
        <span className="hidden lg:block text-sm">{label}</span>
    </button>
);

export default Layout;
