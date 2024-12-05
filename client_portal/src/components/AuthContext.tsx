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
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    console.log("AuthProvider useEffect triggered");

    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const savedContractId = localStorage.getItem('contract_id');
    const tokenExpiration = localStorage.getItem('token_expiration');

    console.log("Access Token:", accessToken);
    console.log("Refresh Token:", refreshToken);
    console.log("Saved Contract ID:", savedContractId);
    console.log("Token Expiration:", tokenExpiration);

    const now = new Date().getTime();
    if (accessToken && savedContractId && tokenExpiration && now < parseInt(tokenExpiration)) {
      console.log("Token is valid");
      setIsAuthenticated(true);
      setContractId(savedContractId);

      // Start periodic token refresh
      startTokenRefresh();
    } else {
      console.log("No valid token or token expired");
      logout();
    }

    setIsLoading(false);
  }, []);

  const startTokenRefresh = () => {
    const refreshInterval = 15 * 60 * 1000; // Refresh every 15 minutes
    const interval = setInterval(async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        console.error("No refresh token available for token refresh.");
        logout();
        return;
      }

      try {
        const response = await fetch('https://www.enet2.com/api/token/refresh/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh: refreshToken }),
        });

        if (response.ok) {
          const data = await response.json();
          const newExpirationTime = new Date().getTime() + 60 * 60 * 1000; // 1 hour
          localStorage.setItem('access_token', data.access);
          localStorage.setItem('token_expiration', newExpirationTime.toString());
          console.log("Token refreshed successfully.");
        } else {
          console.error("Failed to refresh token, logging out.");
          logout();
        }
      } catch (error) {
        console.error("Error during token refresh:", error);
        logout();
      }
    }, refreshInterval);

    // Clear the interval on logout
    return () => clearInterval(interval);
  };

  const login = (accessToken: string, contractId: string) => {
    console.log("Logging in with token and contract ID:", accessToken, contractId);

    const expirationTime = new Date().getTime() + 60 * 60 * 1000; // 1 hour
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('contract_id', contractId);
    localStorage.setItem('token_expiration', expirationTime.toString());

    console.log("Token expiration set to:", expirationTime);

    setIsAuthenticated(true);
    setContractId(contractId);

    startTokenRefresh(); // Start refreshing tokens
  };

  const logout = () => {
    console.log("Logging out");

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('contract_id');
    localStorage.removeItem('token_expiration');

    setIsAuthenticated(false);
    setContractId(null);

    // Clear token refresh interval
    clearInterval(startTokenRefresh as any);
  };

  // Render a loading state until the authentication check is complete
  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, contractId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
