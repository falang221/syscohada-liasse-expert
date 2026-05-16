"use client";

import { Upload, FileText, BarChart3, ShieldCheck, Loader2, LogOut, User as UserIcon } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";

export default function Home() {
  const { user, token, logout, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authLoading && !token) {
      router.push("/login");
    }
  }, [token, authLoading, router]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadAndGenerate(file);
    }
  };

  const uploadAndGenerate = async (file: File) => {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError("Veuillez sélectionner un fichier Excel (.xlsx ou .xls)");
      return;
    }

    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/generate-liasse", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 401) {
          logout();
          return;
        }
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || "Erreur lors de la génération de la liasse");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Liasse_${file.name.replace(/\.[^/.]+$/, "")}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (authLoading || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50">
        <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
      </div>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24 bg-secondary-50">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          SYSCOHADA&nbsp;
          <code className="font-bold text-primary-600">Liasse Expert</code>
        </p>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-xl border border-secondary-200 shadow-sm">
            <UserIcon className="w-4 h-4 text-secondary-500" />
            <span className="text-secondary-700 font-medium">{user?.username}</span>
            <span className="text-[10px] bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">{user?.role}</span>
          </div>
          <button 
            onClick={logout}
            className="flex items-center space-x-2 text-secondary-500 hover:text-red-600 transition-colors p-2"
            title="Déconnexion"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight text-secondary-900 sm:text-6xl">
          Analyse Intelligente de <span className="text-primary-600">Liasses Fiscales</span>
        </h1>
        <p className="mt-6 text-lg leading-8 text-secondary-600 max-w-2xl">
          Bonjour {user?.username}, automatisez l'extraction et l'analyse de vos liasses fiscales SYSCOHADA.
        </p>

        <div className="mt-12 w-full max-w-xl">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept=".xlsx,.xls" 
            className="hidden" 
          />
          <div 
            className="relative group cursor-pointer"
            onClick={() => !isLoading && fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const file = e.dataTransfer.files[0];
              if (file) uploadAndGenerate(file);
            }}
          >
            <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-primary-400 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className={`relative px-7 py-10 bg-white ring-1 ring-gray-900/5 rounded-2xl leading-none flex flex-col items-center justify-center space-y-4 border-2 border-dashed ${isDragging ? 'border-primary-600 bg-primary-50' : 'border-primary-200 hover:border-primary-400'} transition-colors`}>
              <div className="bg-primary-50 p-4 rounded-full">
                {isLoading ? (
                  <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
                ) : (
                  <Upload className="w-10 h-10 text-primary-600" />
                )}
              </div>
              <div className="text-center">
                <p className="text-xl font-semibold text-secondary-900">
                  {isLoading ? "Génération en cours..." : "Déposez votre Balance Générale (Excel)"}
                </p>
                <p className="text-sm text-secondary-500 mt-2">
                  Format .xlsx ou .xls supporté
                </p>
              </div>
              <button 
                disabled={isLoading}
                className="bg-primary-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Traitement..." : "Sélectionner un fichier"}
              </button>
            </div>
          </div>
          {error && (
            <p className="mt-4 text-red-600 text-sm font-medium">{error}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full mt-12 pb-24">
        {/* Same info grid as before */}
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <div className="bg-primary-50 p-3 rounded-lg mb-4">
            <FileText className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-bold text-secondary-900">Import Excel</h3>
          <p className="text-secondary-600 text-sm mt-2">
            Reconnaissance précise de votre balance générale et grand livre.
          </p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <div className="bg-primary-50 p-3 rounded-lg mb-4">
            <BarChart3 className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-bold text-secondary-900">Analyse Financière</h3>
          <p className="text-secondary-600 text-sm mt-2">
            Mapping automatique des comptes selon le plan SYSCOHADA.
          </p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <div className="bg-primary-50 p-3 rounded-lg mb-4">
            <ShieldCheck className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-bold text-secondary-900">Export PDF Officiel</h3>
          <p className="text-secondary-600 text-sm mt-2">
            Génération de la liasse au format requis par la DGID.
          </p>
        </div>
      </div>
    </main>
  );
}
