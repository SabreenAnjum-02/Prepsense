'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Camera, Mic, Lock, User, Mail, ArrowRight } from 'lucide-react';

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    target_role: 'Software Engineer',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let res;
      if (isLogin) {
        // OAuth2 Password Request Form format for FastAPI
        const params = new URLSearchParams();
        params.append('username', formData.email);
        params.append('password', formData.password);

        res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: params,
        });
      } else {
        // JSON format for Registration
        res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        });
      }

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data = await res.json();
      // Store token in localStorage
      localStorage.setItem('prepsense_token', data.access_token);
      localStorage.setItem('prepsense_user_name', data.name);
      
      // Redirect to intake page
      router.push('/intake');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center text-teal-400 mb-6">
          <Camera className="w-10 h-10 mr-2" />
          <Mic className="w-10 h-10" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
          PrepSense AI
        </h2>
        <p className="mt-2 text-center text-sm text-slate-400">
          Your Intelligent Interview Copilot
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800 py-8 px-4 shadow sm:rounded-lg sm:px-10 border border-slate-700">
          <div className="flex justify-between mb-8 border-b border-slate-700 pb-2">
            <button
              className={`text-lg font-medium transition-colors ${isLogin ? 'text-teal-400 border-b-2 border-teal-400' : 'text-slate-400 hover:text-white'}`}
              onClick={() => { setIsLogin(true); setError(''); }}
            >
              Sign In
            </button>
            <button
              className={`text-lg font-medium transition-colors ${!isLogin ? 'text-teal-400 border-b-2 border-teal-400' : 'text-slate-400 hover:text-white'}`}
              onClick={() => { setIsLogin(false); setError(''); }}
            >
              Register
            </button>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded mb-6 text-sm">
              {error}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            {!isLogin && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-300">Full Name</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User className="h-5 w-5 text-slate-500" />
                    </div>
                    <input
                      type="text"
                      required
                      className="block w-full pl-10 bg-slate-900 border border-slate-700 rounded-md py-2 text-white placeholder-slate-500 focus:ring-teal-500 focus:border-teal-500 sm:text-sm"
                      placeholder="John Doe"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300">Target Role</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <select
                      className="block w-full bg-slate-900 border border-slate-700 rounded-md py-2 px-3 text-white focus:ring-teal-500 focus:border-teal-500 sm:text-sm"
                      value={formData.target_role}
                      onChange={(e) => setFormData({ ...formData, target_role: e.target.value })}
                    >
                      <option>Software Engineer</option>
                      <option>Data Scientist</option>
                      <option>Product Manager</option>
                      <option>Frontend Developer</option>
                    </select>
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300">Email address</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="email"
                  required
                  className="block w-full pl-10 bg-slate-900 border border-slate-700 rounded-md py-2 text-white placeholder-slate-500 focus:ring-teal-500 focus:border-teal-500 sm:text-sm"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300">Password</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="password"
                  required
                  className="block w-full pl-10 bg-slate-900 border border-slate-700 rounded-md py-2 text-white placeholder-slate-500 focus:ring-teal-500 focus:border-teal-500 sm:text-sm"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-slate-900 bg-teal-400 hover:bg-teal-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-colors disabled:opacity-50"
              >
                {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
                {!loading && <ArrowRight className="ml-2 w-4 h-4" />}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
