'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextProps {
  isAuthenticated: boolean;
  contractId: string | null;
  login: (accessToken: string, contractId: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [contractId, setContractId] = useState<string | null>(null);

  useEffect(() => {
    const accessToken = localStorage.getItem('access_token');
    const savedContractId = localStorage.getItem('contract_id');
    const tokenExpiration = localStorage.getItem('token_expiration');

    if (accessToken && savedContractId && tokenExpiration) {
      const now = new Date().getTime();
      if (now < parseInt(tokenExpiration)) {
        setIsAuthenticated(true);
        setContractId(savedContractId);
      } else {
        console.log('Token has expired');
        logout(); // Automatically log out if the token has expired
      }
    } else {
      console.log('No valid token found, setting isAuthenticated to false');
      setIsAuthenticated(false);
    }
  }, []);

  const login = (accessToken: string, contractId: string) => {
    const expirationTime = new Date().getTime() + 60 * 60 * 1000; // Token expires in 1 hour
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('contract_id', contractId);
    localStorage.setItem('token_expiration', expirationTime.toString());
    setIsAuthenticated(true);
    setContractId(contractId);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('contract_id');
    localStorage.removeItem('token_expiration');
    setIsAuthenticated(false);
    setContractId(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, contractId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
