"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Loader2, Lock, User as UserIcon } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    try {
      const response = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Identifiants incorrects");
      }

      const data = await response.json();
      login(data.access_token, { username, role: data.role });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-secondary-100">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center p-3 bg-primary-50 rounded-xl mb-4">
            <Lock className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-3xl font-bold text-secondary-900">Connexion</h1>
          <p className="text-secondary-500 mt-2">Accédez à votre espace Liasse-Expert</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">Nom d'utilisateur</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <UserIcon className="h-5 w-5 text-secondary-400" />
              </div>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-secondary-200 rounded-xl leading-5 bg-white placeholder-secondary-400 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 sm:text-sm"
                placeholder="Ex: admin"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">Mot de passe</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-secondary-400" />
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-10 pr-3 py-3 border border-secondary-200 rounded-xl leading-5 bg-white placeholder-secondary-400 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 sm:text-sm"
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm font-medium">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-600 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : "Se connecter"}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-secondary-100 text-center">
          <p className="text-xs text-secondary-400 uppercase tracking-widest font-semibold">
            SYSCOHADA Liasse-Expert
          </p>
        </div>
      </div>
    </div>
  );
}
