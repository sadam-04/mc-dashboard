import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    base:'/static/',
    plugins: [react()],
    server: {
        host: 'localhost',
        port: 5173,
        cors: true,
        origin: 'http://localhost:5173',
    },
    build: {
        manifest: true,
        outDir: 'static/dist',
        rollupOptions: {
            input: 'src/main.jsx'
        }
    }
});