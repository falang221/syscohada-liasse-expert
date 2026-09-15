"use client";

import { Upload, FileText, BarChart3, ShieldCheck, Loader2, LogOut, User as UserIcon, FileCheck } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";

export default function Home() {
  const { user, token, logout, isLoading: authLoading } = useAuth();
  const router = useRouter();
  
  const [fileN, setFileN] = useState<File | null>(null);
  const [fileN1, setFileN1] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fileInputNRef = useRef<HTMLInputElement>(null);
  const fileInputN1Ref = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authLoading && !token) {
      router.push("/login");
    }
  }, [token, authLoading, router]);

  const handleGenerate = async () => {
    if (!fileN) {
      setError("Veuillez sélectionner au moins la balance de l'année N.");
      return;
    }

    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file_n", fileN);
    if (fileN1) {
      formData.append("file_n_1", fileN1);
    }

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
      const a = document.body.appendChild(document.createElement("a"));
      a.href = url;
      a.download = `Liasse_Expert_${fileN.name.replace(/\.[^/.]+$/, "")}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
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
    <main className="flex min-h-screen flex-col items-center p-8 bg-secondary-50">
      {/* Header */}
      <div className="z-10 max-w-5xl w-full flex items-center justify-between font-mono text-sm mb-12">
        <p className="flex items-center space-x-2 border-b border-gray-300 bg-white p-4 rounded-xl border shadow-sm">
          <span className="font-bold text-primary-600">SYSCOHADA</span>
          <span className="text-secondary-900">Liasse Expert</span>
        </p>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-xl border border-secondary-200 shadow-sm">
            <UserIcon className="w-4 h-4 text-secondary-500" />
            <span className="text-secondary-700 font-medium">{user?.username}</span>
            <span className="text-[10px] bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">{user?.role}</span>
          </div>
          <button onClick={logout} className="text-secondary-500 hover:text-red-600 p-2" title="Déconnexion">
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center text-center max-w-4xl w-full">
        <h1 className="text-4xl font-extrabold tracking-tight text-secondary-900 mb-4">
          Génération de Liasse <span className="text-primary-600">Comparatative N-1</span>
        </h1>
        <p className="text-lg text-secondary-600 mb-12">
          Uploadez vos balances pour obtenir un document conforme aux normes DGID.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full mb-12">
          {/* Box Year N */}
          <div 
            onClick={() => fileInputNRef.current?.click()}
            className={`p-8 bg-white rounded-2xl border-2 border-dashed transition-all cursor-pointer ${fileN ? 'border-primary-600 bg-primary-50' : 'border-secondary-200 hover:border-primary-400'}`}
          >
            <input type="file" ref={fileInputNRef} className="hidden" accept=".xlsx,.xls" onChange={(e) => setFileN(e.target.files?.[0] || null)} />
            <div className="flex flex-col items-center space-y-4">
              <div className={`p-3 rounded-full ${fileN ? 'bg-primary-600 text-white' : 'bg-secondary-100 text-secondary-400'}`}>
                {fileN ? <FileCheck className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
              </div>
              <div>
                <p className="font-bold text-secondary-900">Balance Année N</p>
                <p className="text-xs text-secondary-500 mt-1">{fileN ? fileN.name : "Obligatoire (.xlsx)"}</p>
              </div>
            </div>
          </div>

          {/* Box Year N-1 */}
          <div 
            onClick={() => fileInputN1Ref.current?.click()}
            className={`p-8 bg-white rounded-2xl border-2 border-dashed transition-all cursor-pointer ${fileN1 ? 'border-primary-600 bg-primary-50' : 'border-secondary-200 hover:border-primary-400'}`}
          >
            <input type="file" ref={fileInputN1Ref} className="hidden" accept=".xlsx,.xls" onChange={(e) => setFileN1(e.target.files?.[0] || null)} />
            <div className="flex flex-col items-center space-y-4">
              <div className={`p-3 rounded-full ${fileN1 ? 'bg-primary-600 text-white' : 'bg-secondary-100 text-secondary-400'}`}>
                {fileN1 ? <FileCheck className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
              </div>
              <div>
                <p className="font-bold text-secondary-900">Balance Année N-1</p>
                <p className="text-xs text-secondary-500 mt-1">{fileN1 ? fileN1.name : "Optionnel (.xlsx)"}</p>
              </div>
            </div>
          </div>
        </div>

        {error && <p className="mb-6 text-red-600 text-sm font-medium bg-red-50 px-4 py-2 rounded-lg">{error}</p>}

        <button 
          onClick={handleGenerate}
          disabled={isLoading || !fileN}
          className="w-full max-w-md bg-primary-600 text-white py-4 rounded-2xl font-bold text-lg hover:bg-primary-700 transition-all shadow-lg shadow-primary-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3"
        >
          {isLoading ? (
            <><Loader2 className="w-6 h-6 animate-spin" /> <span>Traitement en cours...</span></>
          ) : (
            <span>Générer la Liasse Officielle</span>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full mt-20">
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <FileText className="w-6 h-6 text-primary-600 mb-3" />
          <h3 className="font-bold text-secondary-900 text-sm">Mapping OHADA</h3>
          <p className="text-secondary-500 text-xs mt-1">Classification automatique des comptes 1 à 8.</p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <BarChart3 className="w-6 h-6 text-primary-600 mb-3" />
          <h3 className="font-bold text-secondary-900 text-sm">Calcul de Marges</h3>
          <p className="text-secondary-500 text-xs mt-1">Résultat net et masses bilancielles instantanés.</p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <ShieldCheck className="w-6 h-6 text-primary-600 mb-3" />
          <h3 className="font-bold text-secondary-900 text-sm">Gabarit DGID</h3>
          <p className="text-secondary-500 text-xs mt-1">Export PDF certifié conforme aux normes Sénégalaises.</p>
        </div>
      </div>
    </main>
  );
}
