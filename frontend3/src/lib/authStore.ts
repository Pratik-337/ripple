import { create } from 'zustand';
import { UserProfile, authApi } from './api';

interface AuthState {
    accessToken: string | null;
    user: UserProfile | null;
    isInitialized: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (name: string, email: string, password: string) => Promise<void>;
    loginGithub: () => void;
    logout: () => Promise<void>;
    refresh: () => Promise<void>;
}

export const authStore = create<AuthState>((set, get) => ({
    accessToken: null,
    user: null,
    isInitialized: false,

    login: async (email, password) => {
        const data = await authApi.login(email, password);
        set({ accessToken: data.access_token, user: data.user, isInitialized: true });
    },

    register: async (name, email, password) => {
        const data = await authApi.register(name, email, password);
        set({ accessToken: data.access_token, user: data.user, isInitialized: true });
    },

    loginGithub: () => {
        const baseUrl = (import.meta as any).env?.VITE_API_URL ?? 'http://localhost:8000/api/v1';
        window.location.href = `${baseUrl}/auth/github`;
    },

    logout: async () => {
        try {
            await authApi.logout();
        } catch (e) {
            // ignore
        }
        set({ accessToken: null, user: null, isInitialized: true });
        window.location.href = '/';
    },

    refresh: async () => {
        const data = await authApi.me();
        set({ accessToken: data.access_token, user: data.user, isInitialized: true });
    }
}));
