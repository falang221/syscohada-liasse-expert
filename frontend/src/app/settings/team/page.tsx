"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Users, UserPlus, Trash2, ShieldCheck, User as UserIcon, Loader2 } from "lucide-react";
import Modal from "@/components/Modal";
import { api } from "@/lib/api";

export default function TeamPage() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Creation form state
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("COLLABORATOR");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user && user.role !== 'ADMIN') {
      router.push("/dashboard");
    } else {
      fetchMembers();
    }
  }, [user, router]);

  const fetchMembers = async () => {
    try {
      const data = await api.get("/users/", token);
      setMembers(data);
    } catch (err) {
      console.error("Erreur lors du chargement de l'équipe", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/users/", { username: newUsername, password: newPassword, role: newRole }, token);
      setIsModalOpen(false);
      setNewUsername("");
      setNewPassword("");
      fetchMembers();
    } catch (err) {
      alert("Erreur lors de l'ajout du membre");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (confirm("Êtes-vous sûr de vouloir retirer ce membre ?")) {
      try {
        await api.delete(`/users/${id}`, token);
        fetchMembers();
      } catch (err) {
        alert("Erreur lors de la suppression");
      }
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900 flex items-center gap-2">
            <Users className="text-primary-600" /> Gestion de l'Équipe
          </h1>
          <p className="text-secondary-500">Gérez les accès de vos collaborateurs</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-xl flex items-center gap-2 font-medium hover:bg-primary-700 transition-colors"
        >
          <UserPlus size={18} /> Ajouter un membre
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-secondary-100 shadow-sm overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-secondary-50 border-b border-secondary-100 text-secondary-600 text-sm font-semibold uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4">Utilisateur</th>
              <th className="px-6 py-4">Rôle</th>
              <th className="px-6 py-4">Date d'ajout</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-secondary-100">
            {members.map((member) => (
              <tr key={member.id} className="hover:bg-secondary-50 transition-colors">
                <td className="px-6 py-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-secondary-100 flex items-center justify-center text-secondary-500">
                    <UserIcon size={16} />
                  </div>
                  <span className="font-medium text-secondary-900">{member.username}</span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    member.role === 'ADMIN' ? 'bg-primary-100 text-primary-700' : 'bg-secondary-100 text-secondary-700'
                  }`}>
                    {member.role}
                  </span>
                </td>
                <td className="px-6 py-4 text-secondary-500 text-sm">
                  {new Date(member.createdAt).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 text-right">
                  {member.id !== user?.id && (
                    <button 
                      onClick={() => handleDelete(member.id)}
                      className="text-secondary-400 hover:text-red-600 transition-colors p-2"
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        title="Ajouter un nouveau membre"
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">Nom d'utilisateur</label>
            <input 
              type="text" 
              required
              value={newUsername}
              onChange={e => setNewUsername(e.target.value)}
              className="w-full px-4 py-2 border border-secondary-200 rounded-xl focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
              placeholder="Ex: assistant_cm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">Mot de passe provisoire</label>
            <input 
              type="password" 
              required
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              className="w-full px-4 py-2 border border-secondary-200 rounded-xl focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
              placeholder="••••••••"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-1">Rôle</label>
            <select 
              value={newRole}
              onChange={e => setNewRole(e.target.value)}
              className="w-full px-4 py-2 border border-secondary-200 rounded-xl focus:ring-2 focus:ring-primary-600 focus:border-primary-600 outline-none"
            >
              <option value="COLLABORATOR">Collaborateur (Opérationnel)</option>
              <option value="ADMIN">Administrateur (Gestion complète)</option>
            </select>
          </div>
          <button 
            type="submit" 
            disabled={submitting}
            className="w-full bg-primary-600 text-white py-3 rounded-xl font-bold hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? "Création..." : "Créer le compte"}
          </button>
        </form>
      </Modal>
    </div>
  );
}
