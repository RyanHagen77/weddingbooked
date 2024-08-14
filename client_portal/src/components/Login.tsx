import React, { useState, FormEvent } from 'react';
import axios from 'axios';
import Image from 'next/image';
import { useAuth } from '../components/AuthContext';

interface LoginProps {
  onLogin: () => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string>('');
  const { login } = useAuth();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    try {
      const response = await axios.post('https://www.enet2.com/contracts/api/token/', {
        username,
        password,
      });

      const accessToken = response.data.access;
      const contractId = response.data.contract_id;

      // Call login function to update the AuthContext
      login(accessToken, contractId);
      onLogin(); // Notify parent that login was successful

    } catch (error) {
      setError('Login failed. Please check your credentials.');
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-lightpink">
      <div className="bg-white p-8 rounded shadow-md w-full max-w-md">
        <div className="flex justify-center mb-6">
          <Image src="/client_portal/Final_Logo.png" alt="Essence Logo" width={100} height={100} layout="fixed" />
        </div>
        <h2 className="text-2xl font-bold text-center mb-6 text-black">Login</h2>
        {error && <p className="text-red-500 text-center">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-gray-700">Username:</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded mt-1"
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-gray-700">Password:</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded mt-1"
              required
            />
          </div>
          <button type="submit" className="w-full bg-black text-white py-2 rounded hover:bg-gray-800 transition">Login</button>
        </form>
        <div className="mt-4 text-center">
          <a href="https://www.enet2.com/accounts/password_reset/" className="text-pink-700 hover:underline">Forgot Password?</a>
        </div>
      </div>
    </main>
  );
};

export default Login;
