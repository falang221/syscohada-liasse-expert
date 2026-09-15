"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, FilePlus, Settings, LogOut, FileText } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  const menuItems = [
    { name: "Tableau de bord", href: "/dashboard", icon: LayoutDashboard },
    { name: "Mes Clients", href: "/clients", icon: Users },
    { name: "Générer Liasse", href: "/", icon: FilePlus },
    ...(user?.role === "ADMIN"
      ? [{ name: "Mon Équipe", href: "/settings/team", icon: Users }]
      : []),
    { name: "Paramètres", href: "/settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-secondary-200 flex flex-col h-screen sticky top-0">
      <div className="p-6 border-b border-secondary-100">
        <div className="flex items-center space-x-2">
          <div className="bg-primary-600 p-1.5 rounded-lg">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-secondary-900 leading-none">SYSCOHADA</h1>
            <p className="text-[10px] text-secondary-500 font-medium uppercase tracking-wider">Liasse Expert PRO</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all font-medium",
                isActive
                  ? "bg-primary-50 text-primary-700 shadow-sm shadow-primary-100/50"
                  : "text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900"
              )}
            >
              <item.icon className={cn("w-5 h-5", isActive ? "text-primary-600" : "text-secondary-400")} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-secondary-100">
        <div className="bg-secondary-50 rounded-2xl p-4 mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">
              {user?.username?.substring(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-secondary-900 truncate">{user?.username}</p>
              <p className="text-[10px] text-secondary-500 uppercase font-bold tracking-tight">{user?.role}</p>
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center space-x-3 w-full px-3 py-2.5 text-secondary-600 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all font-medium group"
        >
          <LogOut className="w-5 h-5 text-secondary-400 group-hover:text-red-500" />
          <span>Déconnexion</span>
        </button>
      </div>
    </aside>
  );
}
