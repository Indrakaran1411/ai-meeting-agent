'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Video, 
  UploadCloud, 
  Menu, 
  X, 
  Compass,
  Zap,
  Search
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Meetings', href: '/meetings', icon: Video },
    { name: 'Upload Meeting', href: '/upload', icon: UploadCloud },
    { name: 'AI Semantic Search', href: '/search', icon: Search },
  ];

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="flex h-16 items-center justify-between border-b border-border bg-card px-4 md:hidden">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight text-primary">
          <Compass className="h-6 w-6 text-indigo-600 animate-pulse" />
          <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent font-bold">
            Meeting Agent
          </span>
        </Link>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="rounded-md p-2 hover:bg-accent hover:text-accent-foreground focus:outline-none"
        >
          {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile Navigation Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm md:hidden">
          <div className="fixed inset-y-0 left-0 z-50 w-72 border-r border-border bg-card p-6 shadow-lg transition-transform duration-300 ease-in-out">
            <div className="flex items-center justify-between mb-8">
              <Link
                href="/"
                className="flex items-center gap-2 font-semibold tracking-tight text-primary"
                onClick={() => setIsOpen(false)}
              >
                <Compass className="h-6 w-6 text-indigo-600" />
                <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent font-bold">
                  Meeting Agent
                </span>
              </Link>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-md p-1 hover:bg-accent focus:outline-none"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex flex-col gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground",
                      isActive ? "bg-indigo-50 text-indigo-600 hover:bg-indigo-50 hover:text-indigo-600" : "text-muted-foreground"
                    )}
                  >
                    <Icon className={cn("h-4 w-4", isActive ? "text-indigo-600" : "text-muted-foreground")} />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <aside className="hidden w-64 flex-col border-r border-border bg-card p-6 md:flex h-screen sticky top-0">
        <div className="flex items-center gap-2 mb-8 px-2">
          <Compass className="h-6 w-6 text-indigo-600" />
          <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent font-bold text-lg tracking-tight">
            Meeting Agent
          </span>
        </div>
        <nav className="flex-1 flex flex-col gap-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground",
                  isActive 
                    ? "bg-gradient-to-r from-indigo-50 to-indigo-100/50 text-indigo-600 font-semibold" 
                    : "text-muted-foreground"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-indigo-600" : "text-muted-foreground")} />
                {item.name}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto border-t border-border pt-4 px-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 p-3 rounded-lg">
            <Zap className="h-3.5 w-3.5 text-indigo-500 fill-indigo-500" />
            <div>
              <p className="font-semibold text-foreground">AI Worker Active</p>
              <p>v1.0.0 (Next.js 15)</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
