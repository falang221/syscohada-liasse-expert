"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { 
  Upload, 
  FileText, 
  ChevronRight, 
  ChevronLeft, 
  FileCheck, 
  Loader2, 
  Building2, 
  Calendar,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Info,
  Download,
  Plus,
  Minus,
  CheckCircle2,
  Sparkles
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type Step = "selection" | "upload" | "validation" | "ai_commentary" | "final";

interface Client {
  id: string;
  name: string;
}

interface TafireData {
  activite: number;
  investissement: number;
  financement: number;
  variation_tresorerie: number;
  coherence_check: boolean;
}

export default function GenerateWizard() {
  const { token, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<Step>("selection");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string>("");
  const [selectedYear, setSelectedYear] = useState<string>("2024");
  
  const [fileN, setFileN] = useState<File | null>(null);
  const [fileN1, setFileN1] = useState<File | null>(null);
  const fileInputNRef = useRef<HTMLInputElement>(null);
  const fileInputN1Ref = useRef<HTMLInputElement>(null);

  // AI Commentary State
  const [aiCommentary, setAiCommentary] = useState<string>("");

  // TAFIRE State
  const [baseTafire, setBaseTafire] = useState<TafireData | null>(null);
  const [adjustments, setAdjustments] = useState({
    investissement_adj: 0,
    financement_adj: 0
  });

  useEffect(() => {
    if (!authLoading && !token) {
      router.push("/login");
      return;
    }
    if (token) {
      fetchClients();
    }
  }, [token, authLoading, router]);

  const fetchClients = async () => {
    try {
      const data = await apiRequest("/api/clients/", "GET", null, token);
      setClients(data);
    } catch (err: any) {
      console.error("Failed to fetch clients", err);
    }
  };

  const handleAnalyze = async () => {
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
      const response = await fetch("http://localhost:8000/api/analyze-balances", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Erreur lors de l'analyse des balances.");
      }

      const data = await response.json();
      setBaseTafire(data.tafire);
      setAiCommentary(data.ai_commentary || "");
      setStep("validation");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateFinal = async () => {
    setIsLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append("file_n", fileN!);
    if (fileN1) formData.append("file_n_1", fileN1);
    if (selectedClientId) formData.append("client_id", selectedClientId);
    formData.append("exercice", selectedYear);
    formData.append("adjustments", JSON.stringify(adjustments));
    formData.append("ai_commentary", aiCommentary);

    try {
      const response = await fetch("http://localhost:8000/api/generate-liasse", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) throw new Error("Erreur lors de la génération finale.");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.body.appendChild(document.createElement("a"));
      a.href = url;
      const clientName = clients.find(c => c.id === selectedClientId)?.name || "Liasse";
      a.download = `Liasse_${clientName}_${selectedYear}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      setStep("final");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const adjustedNetFlow = (baseTafire?.variation_tresorerie || 0) + 
                          adjustments.investissement_adj + 
                          adjustments.financement_adj;

  if (authLoading) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="max-w-4xl mx-auto p-6 md:p-12">
      {/* Wizard Header */}
      <div className="mb-12">
        <h1 className="text-3xl font-extrabold text-secondary-900 mb-2">Assistant de Génération</h1>
        <p className="text-secondary-500">Suivez les étapes pour générer votre liasse fiscale certifiée.</p>
        
        {/* Progress Bar */}
        <div className="mt-8 flex items-center">
          <div className={cn("flex-1 h-1.5 rounded-full transition-all", step === "selection" ? "bg-primary-600" : "bg-primary-200")} />
          <div className="w-3" />
          <div className={cn("flex-1 h-1.5 rounded-full transition-all", step === "upload" ? "bg-primary-600" : (step === "selection" ? "bg-secondary-100" : "bg-primary-200"))} />
          <div className="w-3" />
          <div className={cn("flex-1 h-1.5 rounded-full transition-all", step === "validation" ? "bg-primary-600" : (["selection", "upload"].includes(step) ? "bg-secondary-100" : "bg-primary-200"))} />
          <div className="w-3" />
          <div className={cn("flex-1 h-1.5 rounded-full transition-all", step === "ai_commentary" ? "bg-primary-600" : (["selection", "upload", "validation"].includes(step) ? "bg-secondary-100" : "bg-primary-200"))} />
          <div className="w-3" />
          <div className={cn("flex-1 h-1.5 rounded-full transition-all", step === "final" ? "bg-primary-600" : "bg-secondary-100")} />
        </div>
      </div>

      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start space-x-3 text-red-600 animate-in fade-in slide-in-from-top-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Step 1: Selection */}
      {step === "selection" && (
        <div className="bg-white rounded-3xl border border-secondary-200 p-8 shadow-sm">
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-bold text-secondary-700 flex items-center">
                <Building2 className="w-4 h-4 mr-2 text-primary-600" />
                Sélectionner le Client
              </label>
              <select 
                value={selectedClientId}
                onChange={(e) => setSelectedClientId(e.target.value)}
                className="w-full p-4 bg-secondary-50 border border-secondary-200 rounded-2xl focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all outline-none"
              >
                <option value="">-- Choisir un client --</option>
                {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-bold text-secondary-700 flex items-center">
                <Calendar className="w-4 h-4 mr-2 text-primary-600" />
                Année d'exercice
              </label>
              <div className="grid grid-cols-3 gap-3">
                {["2023", "2024", "2025"].map(year => (
                  <button
                    key={year}
                    onClick={() => setSelectedYear(year)}
                    className={cn(
                      "p-3 rounded-xl border-2 font-bold transition-all",
                      selectedYear === year 
                        ? "border-primary-600 bg-primary-50 text-primary-700" 
                        : "border-secondary-100 hover:border-secondary-200 text-secondary-500"
                    )}
                  >
                    {year}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-10 flex justify-end">
            <button
              onClick={() => setStep("upload")}
              disabled={!selectedClientId}
              className="px-8 py-3.5 bg-primary-600 text-white rounded-2xl font-bold flex items-center space-x-2 hover:bg-primary-700 disabled:opacity-50 transition-all"
            >
              <span>Continuer</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Upload */}
      {step === "upload" && (
        <div className="bg-white rounded-3xl border border-secondary-200 p-8 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div 
              onClick={() => fileInputNRef.current?.click()}
              className={cn(
                "p-8 rounded-3xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center text-center space-y-4",
                fileN ? "border-primary-600 bg-primary-50" : "border-secondary-200 hover:border-primary-400"
              )}
            >
              <input type="file" ref={fileInputNRef} className="hidden" accept=".xlsx,.xls" onChange={(e) => setFileN(e.target.files?.[0] || null)} />
              <div className={cn("p-4 rounded-full", fileN ? "bg-primary-600 text-white" : "bg-secondary-100 text-secondary-400")}>
                {fileN ? <FileCheck className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
              </div>
              <div>
                <p className="font-bold text-secondary-900">Balance N ({selectedYear})</p>
                <p className="text-xs text-secondary-500 mt-1">{fileN ? fileN.name : "Format .xlsx obligatoire"}</p>
              </div>
            </div>

            <div 
              onClick={() => fileInputN1Ref.current?.click()}
              className={cn(
                "p-8 rounded-3xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center text-center space-y-4",
                fileN1 ? "border-primary-600 bg-primary-50" : "border-secondary-200 hover:border-primary-400"
              )}
            >
              <input type="file" ref={fileInputN1Ref} className="hidden" accept=".xlsx,.xls" onChange={(e) => setFileN1(e.target.files?.[0] || null)} />
              <div className={cn("p-4 rounded-full", fileN1 ? "bg-primary-600 text-white" : "bg-secondary-100 text-secondary-400")}>
                {fileN1 ? <FileCheck className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
              </div>
              <div>
                <p className="font-bold text-secondary-900">Balance N-1 ({parseInt(selectedYear)-1})</p>
                <p className="text-xs text-secondary-500 mt-1">{fileN1 ? fileN1.name : "Recommandé pour TAFIRE"}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <button onClick={() => setStep("selection")} className="px-6 py-3 text-secondary-500 font-bold flex items-center space-x-2">
              <ChevronLeft className="w-5 h-5" />
              <span>Retour</span>
            </button>
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !fileN}
              className="px-8 py-3.5 bg-primary-600 text-white rounded-2xl font-bold flex items-center space-x-2 hover:bg-primary-700 disabled:opacity-50 transition-all shadow-lg shadow-primary-100"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>Analyser & Continuer</span>}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: TAFIRE Validation */}
      {step === "validation" && baseTafire && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-secondary-200 p-8 shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xl font-extrabold text-secondary-900">Validation des Flux TAFIRE</h2>
              <div className={cn(
                "px-4 py-1.5 rounded-full text-xs font-bold flex items-center space-x-1.5",
                baseTafire.coherence_check ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
              )}>
                {baseTafire.coherence_check ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                <span>{baseTafire.coherence_check ? "Structurellement Cohérent" : "Vérification Requis"}</span>
              </div>
            </div>

            {/* Base Flows Display */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
              <div className="p-5 bg-secondary-50 rounded-2xl border border-secondary-100">
                <p className="text-[10px] uppercase font-bold text-secondary-400 tracking-wider mb-2">Activités</p>
                <p className="text-lg font-extrabold text-secondary-900">{baseTafire.activite.toLocaleString()} F</p>
              </div>
              <div className="p-5 bg-secondary-50 rounded-2xl border border-secondary-100">
                <p className="text-[10px] uppercase font-bold text-secondary-400 tracking-wider mb-2">Investissement</p>
                <p className="text-lg font-extrabold text-secondary-900">{baseTafire.investissement.toLocaleString()} F</p>
              </div>
              <div className="p-5 bg-secondary-50 rounded-2xl border border-secondary-100">
                <p className="text-[10px] uppercase font-bold text-secondary-400 tracking-wider mb-2">Financement</p>
                <p className="text-lg font-extrabold text-secondary-900">{baseTafire.financement.toLocaleString()} F</p>
              </div>
            </div>

            {/* Adjustment Wizard */}
            <div className="space-y-8">
              <div className="p-6 bg-primary-50/50 rounded-2xl border border-primary-100 space-y-6">
                <h3 className="text-sm font-bold text-primary-800 flex items-center">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Ajustements Manuel (Flux de Trésorerie)
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-secondary-600">Cessions / Acquisitions (Net)</label>
                    <div className="flex items-center space-x-3">
                      <input 
                        type="number" 
                        value={adjustments.investissement_adj}
                        onChange={(e) => setAdjustments(p => ({...p, investissement_adj: parseFloat(e.target.value) || 0}))}
                        className="flex-1 p-3 bg-white border border-secondary-200 rounded-xl focus:ring-2 focus:ring-primary-500/20 outline-none text-sm font-mono"
                      />
                      <div className="text-secondary-400"><TrendingDown className="w-5 h-5" /></div>
                    </div>
                    <p className="text-[10px] text-secondary-400 italic">Positif pour Cession, Négatif pour Acquisition</p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-bold text-secondary-600">Augmentation / Dividendes</label>
                    <div className="flex items-center space-x-3">
                      <input 
                        type="number" 
                        value={adjustments.financement_adj}
                        onChange={(e) => setAdjustments(p => ({...p, financement_adj: parseFloat(e.target.value) || 0}))}
                        className="flex-1 p-3 bg-white border border-secondary-200 rounded-xl focus:ring-2 focus:ring-primary-500/20 outline-none text-sm font-mono"
                      />
                      <div className="text-secondary-400"><TrendingUp className="w-5 h-5" /></div>
                    </div>
                    <p className="text-[10px] text-secondary-400 italic">Positif pour Augmentation, Négatif pour Dividendes</p>
                  </div>
                </div>
              </div>

              {/* Real-time Preview */}
              <div className="p-8 bg-secondary-900 rounded-3xl text-white flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl shadow-secondary-200">
                <div>
                  <p className="text-secondary-400 text-xs font-bold uppercase tracking-widest mb-1">Variation Nette Finale</p>
                  <p className="text-3xl font-black">{adjustedNetFlow.toLocaleString()} <span className="text-secondary-500 text-xl font-normal">FCFA</span></p>
                </div>
                <div className="flex items-center space-x-2 text-xs font-medium bg-white/10 px-4 py-2 rounded-full">
                  <Info className="w-4 h-4 text-primary-400" />
                  <span>Calculé dynamiquement selon vos ajustements</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <button onClick={() => setStep("upload")} className="px-6 py-3 text-secondary-500 font-bold flex items-center space-x-2">
              <ChevronLeft className="w-5 h-5" />
              <span>Retour aux fichiers</span>
            </button>
            <button
              onClick={() => setStep("ai_commentary")}
              className="px-8 py-3.5 bg-primary-600 text-white rounded-2xl font-bold flex items-center space-x-2 hover:bg-primary-700 transition-all shadow-lg shadow-primary-100"
            >
              <span>Continuer vers l'Analyse</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 4: AI Commentary Review */}
      {step === "ai_commentary" && (
        <div className="bg-white rounded-3xl border border-secondary-200 p-8 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-primary-100 text-primary-600 rounded-xl">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-secondary-900">Analyse de l'Expert IA</h2>
              <p className="text-sm text-secondary-500">Révisez et personnalisez le commentaire généré par l'IA pour votre liasse.</p>
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <label className="text-sm font-bold text-secondary-700 block">
              Commentaire de l'Expert
            </label>
            <textarea
              value={aiCommentary}
              onChange={(e) => setAiCommentary(e.target.value)}
              className="w-full h-80 p-6 bg-secondary-50 border border-secondary-200 rounded-2xl focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all outline-none resize-none font-medium text-secondary-700 leading-relaxed"
              placeholder="Saisissez votre commentaire ici..."
            />
          </div>

          <div className="flex items-center justify-between">
            <button onClick={() => setStep("validation")} className="px-6 py-3 text-secondary-500 font-bold flex items-center space-x-2">
              <ChevronLeft className="w-5 h-5" />
              <span>Retour à la validation</span>
            </button>
            <button
              onClick={handleGenerateFinal}
              disabled={isLoading}
              className="px-8 py-3.5 bg-green-600 text-white rounded-2xl font-bold flex items-center space-x-2 hover:bg-green-700 transition-all shadow-lg shadow-green-100"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><FileText className="w-5 h-5" /> <span>Générer le PDF Final</span></>}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Final */}
      {step === "final" && (
        <div className="bg-white rounded-3xl border border-secondary-200 p-12 shadow-sm text-center">
          <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-12 h-12" />
          </div>
          <h2 className="text-2xl font-black text-secondary-900 mb-2">Liasse Générée avec Succès !</h2>
          <p className="text-secondary-500 mb-10 max-w-sm mx-auto">Votre document PDF a été généré et le téléchargement a normalement débuté.</p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md mx-auto">
            <button 
              onClick={() => {
                setStep("selection");
                setFileN(null);
                setFileN1(null);
              }}
              className="px-6 py-3.5 bg-white border border-secondary-200 rounded-2xl font-bold text-secondary-700 hover:bg-secondary-50 transition-all"
            >
              Nouveau dossier
            </button>
            <button 
              onClick={() => router.push("/dashboard")}
              className="px-6 py-3.5 bg-secondary-900 text-white rounded-2xl font-bold hover:bg-black transition-all"
            >
              Retour au tableau de bord
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
