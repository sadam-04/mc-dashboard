import React from 'react';
import { createRoot } from 'react-dom/client';

const App = () => <div>cuh</div>;

const rootElement = document.getElementById('react-root');
if (rootElement) {
    const root = createRoot(rootElement);
    root.render(<App />);
}