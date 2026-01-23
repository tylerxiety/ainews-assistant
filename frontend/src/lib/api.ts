/**
 * Centralized API configuration
 */

// Backend API URL - consistent across all components
// Use conditional check to allow empty string (relative path) which || would treat as falsy
const envUrl = import.meta.env.VITE_API_URL;
export const API_URL = envUrl !== undefined ? envUrl : 'http://localhost:8080';

/**
 * Helper to build API endpoint URLs
 */
export function apiUrl(path: string): string {
    // Ensure path starts with /
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${API_URL}${normalizedPath}`;
}
