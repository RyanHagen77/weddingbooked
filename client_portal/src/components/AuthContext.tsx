'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

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
  const [isLoading, setIsLoading] = useState<boolean>(true); // Add a loading state

  useEffect(() => {
    console.log("AuthProvider useEffect triggered");

    const accessToken = localStorage.getItem('access_token');
    const savedContractId = localStorage.getItem('contract_id');
    const tokenExpiration = localStorage.getItem('token_expiration');

    console.log("Access Token:", accessToken);
    console.log("Saved Contract ID:", savedContractId);
    console.log("Token Expiration:", tokenExpiration);

    if (accessToken && savedContractId && tokenExpiration) {
      const now = new Date().getTime();
      if (now < parseInt(tokenExpiration)) {
        console.log("Token is valid");
        setIsAuthenticated(true);
        setContractId(savedContractId);
      } else {
        console.log("Token has expired");
        logout(); // Automatically log out if the token has expired
      }
    } else {
      console.log("No valid token found, setting isAuthenticated to false");
      setIsAuthenticated(false);
    }

    setIsLoading(false); // Set loading to false once the check is done
  }, []);

  const login = (accessToken: string, contractId: string) => {
    console.log("Logging in with token and contract ID:", accessToken, contractId);

    const expirationTime = new Date().getTime() + 60 * 60 * 1000; // Token expires in 1 hour
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('contract_id', contractId);
    localStorage.setItem('token_expiration', expirationTime.toString());

    console.log("Token expiration set to:", expirationTime);

    setIsAuthenticated(true);
    setContractId(contractId);
  };

  const logout = () => {
    console.log("Logging out");

    localStorage.removeItem('access_token');
    localStorage.removeItem('contract_id');
    localStorage.removeItem('token_expiration');

    setIsAuthenticated(false);
    setContractId(null);
  };

  // Render a loading state until the authentication check is complete
  if (isLoading) {
    return <div>Loading...</div>; // You can customize this loading state as needed
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, contractId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
