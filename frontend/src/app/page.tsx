import { Upload, FileText, BarChart3, ShieldCheck } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-height-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          SYSCOHADA&nbsp;
          <code className="font-bold text-primary-600">Liasse Expert</code>
        </p>
      </div>

      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight text-secondary-900 sm:text-6xl">
          Analyse Intelligente de <span className="text-primary-600">Liasses Fiscales</span>
        </h1>
        <p className="mt-6 text-lg leading-8 text-secondary-600 max-w-2xl">
          Automatisez l'extraction et l'analyse de vos liasses fiscales SYSCOHADA.
          Précision, rapidité et conformité garanties par l'IA.
        </p>

        <div className="mt-12 w-full max-w-xl">
          <div className="relative group cursor-pointer">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-primary-400 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative px-7 py-10 bg-white ring-1 ring-gray-900/5 rounded-2xl leading-none flex flex-col items-center justify-center space-y-4 border-2 border-dashed border-primary-200 hover:border-primary-400 transition-colors">
              <div className="bg-primary-50 p-4 rounded-full">
                <Upload className="w-10 h-10 text-primary-600" />
              </div>
              <div className="text-center">
                <p className="text-xl font-semibold text-secondary-900">
                  Déposez votre liasse fiscale ici
                </p>
                <p className="text-sm text-secondary-500 mt-2">
                  Format PDF supporté (Max 20 Mo)
                </p>
              </div>
              <button className="bg-primary-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors">
                Sélectionner un fichier
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full mt-12 pb-24">
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <div className="bg-primary-50 p-3 rounded-lg mb-4">
            <FileText className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-bold text-secondary-900">Extraction OCR</h3>
          <p className="text-secondary-600 text-sm mt-2">
            Reconnaissance précise des tableaux financiers et des notes annexes.
          </p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <div className="bg-primary-50 p-3 rounded-lg mb-4">
            <BarChart3 className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-bold text-secondary-900">Analyse Financière</h3>
          <p className="text-secondary-600 text-sm mt-2">
            Calcul automatique des ratios et détection des anomalies comptables.
          </p>
        </div>
        <div className="p-6 bg-white rounded-xl shadow-sm border border-secondary-100 flex flex-col items-center text-center">
          <div className="bg-primary-50 p-3 rounded-lg mb-4">
            <ShieldCheck className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="text-lg font-bold text-secondary-900">Conformité</h3>
          <p className="text-secondary-600 text-sm mt-2">
            Vérification stricte par rapport au référentiel SYSCOHADA révisé.
          </p>
        </div>
      </div>
    </main>
  );
}
