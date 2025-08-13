import React, { useState, FormEvent } from 'react';
import axios from 'axios';
import Image from 'next/image';
import { useAuth } from '../components/AuthContext';

interface LoginProps {
  onLogin: () => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const { login } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post('https://www.weddingbooked.app/users/api/token/', {
        email,
        password,
      });
      const { access, refresh, contract_id: contractId } = response.data;
      login(access, refresh, contractId);
      onLogin();
    } catch (err) {
      console.error('Login error:', err);
      setError('Login failed. Please check your credentials.');
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 bg-lightpink/20 dark:bg-neutral-900">
      <div className="w-full max-w-md rounded-2xl shadow-md bg-white dark:bg-neutral-800 border border-lightpink/40 dark:border-lightpink/30 p-8">
        <div className="flex justify-center mb-6">
          <Image
            src="/client_portal/Final_Logo.png"
            alt="Essence Logo"
            width={100}
            height={100}
            className="dark:invert"
            priority
          />
        </div>

        <h2 className="text-2xl font-bold text-center mb-6 text-neutral-900 dark:text-neutral-100">
          Login
        </h2>

        {error && (
          <p className="text-center text-red-600 dark:text-red-400 mb-4">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-neutral-700 dark:text-neutral-200"
            >
              Email
            </label>
            <input
              type="email"
              id="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 dark:border-neutral-700
                         bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100
                         placeholder-neutral-400 dark:placeholder-neutral-500 px-3 py-2
                         focus:outline-none focus:ring-2 focus:ring-lightpink-dark focus:border-lightpink-dark
                         [color-scheme:light]"
              required
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-neutral-700 dark:text-neutral-200"
            >
              Password
            </label>
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-neutral-300 dark:border-neutral-700
                         bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100
                         placeholder-neutral-400 dark:placeholder-neutral-500 px-3 py-2
                         focus:outline-none focus:ring-2 focus:ring-lightpink-dark focus:border-lightpink-dark
                         [color-scheme:light]"
              required
            />
            <label className="mt-3 flex items-center gap-2 select-none text-neutral-700 dark:text-neutral-200">
              <input
                type="checkbox"
                id="showPassword"
                checked={showPassword}
                onChange={() => setShowPassword(!showPassword)}
                className="h-4 w-4 rounded border-neutral-300 dark:border-neutral-600 text-lightpink-dark focus:ring-lightpink-dark"
              />
              <span>Show password</span>
            </label>
          </div>

          <button
            type="submit"
            className="w-full rounded-md bg-lightpink-dark text-white py-2.5 transition
                       hover:brightness-110 dark:hover:brightness-115
                       focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-lightpink-dark
                       dark:focus:ring-offset-neutral-900"
          >
            Login
          </button>
        </form>

        <div className="mt-6 text-center">
          <a
            href="https://www.weddingbooked.app/users/password_reset/"
            className="text-lightpink-dark hover:brightness-110 hover:underline"
          >
            Forgot Password?
          </a>
        </div>
      </div>
    </main>
  );
};

export default Login;
